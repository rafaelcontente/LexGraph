"""Contrato de dados do corpus (Módulo 0).
Camada estrutural: NÃO contém interpretação semântica.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel, ConfigDict, Field, HttpUrl,
    computed_field, field_validator, model_validator,
)

from .canonical import canonical_json, normalizar_texto, sha256_texto

SCHEMA_VERSAO = "1.0.0"


class TipoUnidade(str, Enum):
    ATO = "ato"
    CAPITULO = "capitulo"
    SECCAO = "seccao"
    ARTIGO = "artigo"
    NUMERO = "numero"          # "n.º"
    ALINEA = "alinea"          # "alínea a)"
    SUBALINEA = "subalinea"    # "i)"
    PONTO = "ponto"            # pontos numerados (art. 3.º, anexos)
    CONSIDERANDO = "considerando"
    ANEXO = "anexo"
    APENDICE = "apendice"


PREFIXO: dict[TipoUnidade, str] = {
    TipoUnidade.ATO: "ato", TipoUnidade.CAPITULO: "cap",
    TipoUnidade.SECCAO: "sec", TipoUnidade.ARTIGO: "art",
    TipoUnidade.NUMERO: "par", TipoUnidade.ALINEA: "al",
    TipoUnidade.SUBALINEA: "sub", TipoUnidade.PONTO: "pt",
    TipoUnidade.CONSIDERANDO: "cons", TipoUnidade.ANEXO: "anx",
    TipoUnidade.APENDICE: "apd",
}

# art_6 | art_6_par_2 | art_6_par_2_al_a | art_3_pt_12 | anx_iii_pt_1 | cons_45
ID_RE = re.compile(r"^[a-z]{2,4}(_[a-z0-9]+)+$")
CELEX_RE = re.compile(r"^[03]\d{4}[A-Z]{1,2}\d{4}(-\d{8})?$")


class Base(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, str_strip_whitespace=True,
        validate_assignment=True,
    )


# ---------------------------------------------------------------- temporal

class Vigencia(BaseModel):
    """Validade TEXTUAL da expressão. Intervalo semiaberto [inicio, fim)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    inicio: date
    fim: date | None = None      # None = versão atualmente autoritária

    @model_validator(mode="after")
    def _ordem(self):
        if self.fim is not None and self.fim <= self.inicio:
            raise ValueError("vigencia.fim deve ser estritamente posterior a inicio")
        return self


class Aplicacao(BaseModel):
    """Efeito NORMATIVO. Pode diferir da vigência textual (art. 113.º)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    inicio: date | None = None
    fim: date | None = None
    herdada_de: str | None = None   # unidade_id de onde herda (ex.: art_113)

    @model_validator(mode="after")
    def _coerencia(self):
        if self.fim is not None and self.inicio is None:
            raise ValueError("aplicacao.fim sem aplicacao.inicio")
        if self.fim is not None and self.fim <= self.inicio:
            raise ValueError("aplicacao.fim deve ser posterior a inicio")
        if self.inicio is None and self.herdada_de is None:
            raise ValueError(
                "aplicacao desconhecida: define inicio ou herdada_de "
                "(nulidade silenciosa é proibida)"
            )
        return self


# ---------------------------------------------------------------- proveniência

class Fonte(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ato_id: str                       # reg_2024_1689 | reg_2026_1744
    celex: str                        # 32024R1689 | 02024R1689-20260727
    eli: HttpUrl
    url_oficial: HttpUrl
    lingua: Literal["PT", "EN", "FR", "DE"] = "PT"
    consolidada_em: date | None = None

    @field_validator("celex")
    @classmethod
    def _celex(cls, v: str) -> str:
        if not CELEX_RE.match(v):
            raise ValueError(f"CELEX inválido: {v!r}")
        return v


class Lineage(BaseModel):
    """Apenas campos DETERMINÍSTICOS. data_descarga vive no manifest."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    pipeline_versao: str
    metodo_extracao: Literal["docling", "lxml", "manual", "hibrido"]
    fonte_hash: str = Field(pattern=r"^[a-f0-9]{64}$")   # sha256 do HTML/XML bruto
    extractor_versao: str | None = None                  # ex.: docling==2.x


# ---------------------------------------------------------------- registo

class RegistoCorpus(Base):
    schema_versao: Literal["1.0.0"] = SCHEMA_VERSAO

    unidade_id: str
    tipo: TipoUnidade
    parent_id: str | None = None
    ordem: int = Field(ge=0)
    rotulo: str                       # "Artigo 6.º, n.º 2"
    texto: str = Field(min_length=1)

    vigencia: Vigencia
    aplicacao: Aplicacao
    fonte: Fonte
    lineage: Lineage

    remissoes_raw: tuple[str, ...] = ()   # texto cru; resolução no Módulo 1
    tags: tuple[str, ...] = ()

    @field_validator("unidade_id", "parent_id")
    @classmethod
    def _id(cls, v: str | None) -> str | None:
        if v is not None and not ID_RE.match(v):
            raise ValueError(f"ID fora do padrão canónico: {v!r}")
        return v

    @field_validator("texto")
    @classmethod
    def _normaliza(cls, v: str) -> str:
        return normalizar_texto(v)

    @model_validator(mode="after")
    def _tipo_bate_com_id(self):
        esperado = PREFIXO[self.tipo]
        # o último par tipo/chave do ID tem de corresponder ao tipo declarado
        tokens = self.unidade_id.split("_")
        ultimo_tipo = tokens[-2]
        if ultimo_tipo != esperado:
            raise ValueError(
                f"tipo={self.tipo.value} exige sufixo '{esperado}_', "
                f"ID termina em '{ultimo_tipo}_'"
            )
        if self.tipo is TipoUnidade.ATO and self.parent_id is not None:
            raise ValueError("unidade raiz (ato) não pode ter parent_id")
        return self

    @computed_field
    @property
    def expressao_id(self) -> str:
        return f"{self.unidade_id}@{self.vigencia.inicio.isoformat()}"

    @computed_field
    @property
    def texto_hash(self) -> str:
        return sha256_texto(self.texto)

    @computed_field
    @property
    def conteudo_hash(self) -> str:
        """Identidade semântica do registo. Chave para reviews.jsonl e auditoria."""
        nucleo = {
            "unidade_id": self.unidade_id,
            "tipo": self.tipo.value,
            "texto": self.texto,
            "vigencia": self.vigencia.model_dump(mode="json"),
            "aplicacao": self.aplicacao.model_dump(mode="json"),
            "celex": self.fonte.celex,
        }
        return sha256_texto(canonical_json(nucleo))


# ---------------------------------------------------------------- manifest (volátil)

class AtoDescarregado(Base):
    ato_id: str
    celex: str
    url: HttpUrl
    data_descarga: datetime
    ficheiro: str
    fonte_hash: str
    data_documento: date | None = None
    data_publicacao_jo: date | None = None
    data_entrada_em_vigor: date | None = None
    verificado_fonte_oficial: bool = False   # ← trava de segurança do benchmark


class Manifest(Base):
    schema_versao: Literal["1.0.0"] = SCHEMA_VERSAO
    corpus_versao: str
    licenca: str
    atos: tuple[AtoDescarregado, ...]