from dataclasses import dataclass
from src.domain.entities.diagnostico import Diagnostico, PorteEmpresa

@dataclass
class AcaoChecklist:
    descricao: str
    responsavel: str
    prazo: str
    criticidade: str

@dataclass
class FrenteTrabalho:
    nome: str
    acoes: list[AcaoChecklist]

@dataclass
class ImpactoDepartamento:
    departamento: str
    impacto_resumo: str
    criticidade: str

class ConsultoriaService:
    """
    Serviço que traduz o perfil da empresa (Porte, Regime) em um
    Checklist de Implantação da CBS (Decreto 12.955/2026) e Matriz de Impacto.
    """

    @staticmethod
    def gerar_checklist(diagnostico: Diagnostico) -> list[FrenteTrabalho]:
        frentes = []
        
        # Frente 1 - Governança (Para todas as empresas)
        frentes.append(
            FrenteTrabalho(
                nome="Governança e Comitê",
                acoes=[
                    AcaoChecklist("Constituir Comitê Tributário Reforma", "Diretoria", "Out/2025", "Crítica"),
                    AcaoChecklist("Aprovar plano-mestre de implantação", "Comitê", "Nov/2025", "Alta")
                ]
            )
        )

        # Frente 2 - Cadastros e ERP (Maior impacto para grandes empresas)
        if diagnostico.empresa.porte in [PorteEmpresa.GRANDE, PorteEmpresa.MEDIA]:
            frentes.append(
                FrenteTrabalho(
                    nome="TI / ERP / Sistema Fiscal",
                    acoes=[
                        AcaoChecklist("Levantar gap funcional do ERP", "TI / Fiscal", "Dez/2025", "Crítica"),
                        AcaoChecklist("Aplicar patches fornecidos pelo ERP", "TI", "Mar/2026", "Crítica")
                    ]
                )
            )
            frentes.append(
                FrenteTrabalho(
                    nome="Cadastros Mestres",
                    acoes=[
                        AcaoChecklist("Revisar 100% do cadastro de itens (NCM, GTIN)", "Cadastro / Fiscal", "Mar/2026", "Crítica"),
                        AcaoChecklist("Atualizar CST CBS por item/serviço", "Fiscal", "Mar/2026", "Crítica")
                    ]
                )
            )

        # Frente 3 - Contratos (Serviços e Atacado sentem mais)
        frentes.append(
            FrenteTrabalho(
                nome="Contratos e Cláusulas Tributárias",
                acoes=[
                    AcaoChecklist("Padronizar nova cláusula tributária (gross-up CBS)", "Jurídico", "Fev/2026", "Crítica"),
                    AcaoChecklist("Negociar aditivos com fornecedores estratégicos", "Compras", "Mar/2026", "Alta")
                ]
            )
        )

        return frentes

    @staticmethod
    def gerar_matriz_impacto(diagnostico: Diagnostico) -> list[ImpactoDepartamento]:
        matriz = [
            ImpactoDepartamento("Fiscal", "Apuração paralela PIS/COFINS e CBS ao longo de 2026", "Crítica"),
            ImpactoDepartamento("Comercial", "Recalibragem de Pricing e atualização de tabelas de preços com novas alíquotas", "Alta"),
            ImpactoDepartamento("TI", "Adequação dos sistemas ERP e emissão de notas fiscais com layout CBS", "Crítica"),
            ImpactoDepartamento("Jurídico", "Revisão e aditivo de todos os contratos vigentes", "Média")
        ]
        return matriz
