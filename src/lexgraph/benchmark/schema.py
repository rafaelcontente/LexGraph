"""Contrato do golden dataset (Módulo 2)."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Categoria(str, Enum):
    FACTUAL_SIMPLES = "factual_simples"
    MULTI_SALTO = "multi_salto"
    TEMPORAL = "temporal"
    DEFINICAO = "definicao"
    NEGACAO = "negacao"
    PREMISSA_FALSA = "premissa_falsa"
    FORA_CORPUS = "fora_corpus"


class Estado(str, Enum):
    PENDENTE = "pendente"
    VERIFICADO = "verificado"
    REJEITADO = "rejeitado"


class Particao(str, Enum):
    DEV = "dev"
    CALIBRACAO = "calibracao"
    TESTE = "teste"
    CONTAMINACAO = "contaminacao"


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Evidencia(_Base):
    celex: str
    localizador: str = Field(min_length=1)
    citacao_literal: str = Field(min_length=1)
    url: HttpUrl
    unidade_id: str | None = None


class Questao(_Base):
    id: str = Field(pattern=r"^q_\d{3}$")
    categoria: Categoria
    pergunta: str = Field(min_length=10)

    resposta_esperada: str | None = None
    tipo_resposta: Literal["data", "sim_nao", "texto_curto", "lista", "sem_resposta"]
    asof: date | None = None

    evidencias: tuple[Evidencia, ...] = ()
    procura_negativa: str | None = None
    premissa_declarada: str | None = None

    dificuldade: Literal["facil", "media", "dificil"]
    pos_cutoff: bool
    particao: Particao

    estado: Estado = Estado.PENDENTE
    verificado_por: str | None = None
    verificado_em: date | None = None
    notas: str | None = None

    @model_validator(mode="after")
    def _coerencia(self):
        c = self.categoria

        if c is Categoria.FORA_CORPUS:
            if self.resposta_esperada is not None:
                raise ValueError("fora_corpus nao tem resposta esperada")
            if self.tipo_resposta != "sem_resposta":
                raise ValueError("fora_corpus exige tipo_resposta='sem_resposta'")
            if not self.procura_negativa:
                raise ValueError("fora_corpus exige procura_negativa documentada")
        else:
            if not self.resposta_esperada:
                raise ValueError("pergunta respondivel exige resposta_esperada")
            if not self.evidencias:
                raise ValueError("pergunta respondivel exige pelo menos uma evidencia")

        if c is Categoria.TEMPORAL and self.asof is None:
            raise ValueError("pergunta temporal exige asof")
        if c is not Categoria.TEMPORAL and self.asof is not None:
            raise ValueError("asof so se aplica a perguntas temporais")

        if c is Categoria.PREMISSA_FALSA and not self.premissa_declarada:
            raise ValueError("premissa_falsa exige premissa_declarada")
        if c is Categoria.NEGACAO and not self.procura_negativa:
            raise ValueError("negacao exige procura_negativa documentada")

        if self.estado is Estado.VERIFICADO:
            if not self.verificado_por or not self.verificado_em:
                raise ValueError(
                    "estado=verificado exige verificado_por e verificado_em "
                    "(maker-checker: nao se auto-verifica)"
                )
        if self.estado is Estado.VERIFICADO:
            for ev in self.evidencias:
                alvo = (ev.citacao_literal + " " + ev.localizador).upper()
                if any(m in alvo for m in ("A PREENCHER", "A CONFIRMAR", "PLACEHOLDER", "TODO")):
                    raise ValueError(
                        "estado=verificado com citacao placeholder: " + ev.localizador
                    )
        return self


def ativas(questoes: list[Questao]) -> list[Questao]:
    return [q for q in questoes if q.estado is Estado.VERIFICADO]


def exigir_verificadas(questoes: list[Questao], particao: Particao) -> None:
    """Portao. Chamado antes de qualquer corrida de benchmark."""
    pend = [q.id for q in questoes
            if q.particao is particao and q.estado is not Estado.VERIFICADO]
    if pend:
        raise RuntimeError(
            f"Bloqueado: {len(pend)} perguntas nao verificadas em {particao.value}: "
            f"{', '.join(pend[:10])}"
        )
