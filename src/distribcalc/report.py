"""Geração do artigo em PDF descrevendo a solução distribuída."""
from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _diagram_flowable(width: float = 18 * cm, height: float = 8 * cm) -> Drawing:
    drawing = Drawing(width, height)
    # Client box
    drawing.add(Rect(0.5 * cm, 3.5 * cm, 5 * cm, 3 * cm, strokeColor=colors.darkblue, fillColor=colors.whitesmoke))
    drawing.add(String(1 * cm, 6 * cm, "Cliente", fontSize=12, fillColor=colors.darkblue))
    drawing.add(String(1 * cm, 5.2 * cm, "Thread Principal", fontSize=9))
    drawing.add(String(1 * cm, 4.7 * cm, "Thread de Recepção", fontSize=9))

    # Network arrow
    drawing.add(Line(5.5 * cm, 5 * cm, 8 * cm, 5 * cm, strokeColor=colors.black, strokeWidth=2))
    drawing.add(String(6.1 * cm, 5.3 * cm, "TCP", fontSize=9))

    # Server box
    drawing.add(Rect(8 * cm, 2.8 * cm, 6 * cm, 4.4 * cm, strokeColor=colors.darkgreen, fillColor=colors.aliceblue))
    drawing.add(String(8.4 * cm, 6.6 * cm, "Servidor TCP", fontSize=12, fillColor=colors.darkgreen))
    drawing.add(String(8.4 * cm, 5.8 * cm, "Threads de Sessão", fontSize=9))
    drawing.add(String(8.4 * cm, 5.3 * cm, "Fila lógica de requisições", fontSize=9))

    # Arrow to worker pool
    drawing.add(Line(12.5 * cm, 5 * cm, 15 * cm, 5 * cm, strokeColor=colors.black, strokeWidth=2))

    # Process pool box
    drawing.add(Rect(15 * cm, 3.2 * cm, 5 * cm, 3.6 * cm, strokeColor=colors.darkred, fillColor=colors.mistyrose))
    drawing.add(String(15.4 * cm, 6.3 * cm, "Pool de Processos", fontSize=12, fillColor=colors.darkred))
    drawing.add(String(15.4 * cm, 5.5 * cm, "Executor Multiprocessado", fontSize=9))
    drawing.add(String(15.4 * cm, 5.0 * cm, "Cálculo de Primos", fontSize=9))

    # Return arrow
    drawing.add(Line(15 * cm, 3.7 * cm, 5.5 * cm, 3.7 * cm, strokeColor=colors.gray, strokeWidth=1.5))
    drawing.add(String(9.5 * cm, 3.4 * cm, "Respostas", fontSize=9, fillColor=colors.gray))

    return drawing


def generate_report(output_path: str | Path = "docs/artigo.pdf") -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Heading1Center", parent=styles["Heading1"], alignment=1))
    body = styles["BodyText"]
    body.spaceAfter = 12

    content = []
    content.append(Paragraph("Arquitetura Distribuída para Cálculo de Primos", styles["Heading1Center"]))
    content.append(Spacer(1, 0.5 * cm))

    # Resumo
    content.append(Paragraph("Resumo", styles["Heading2"]))
    content.append(
        Paragraph(
            "Este artigo apresenta uma aplicação cliente-servidor escrita em Python que "
            "explora conceitos de sistemas distribuídos, concorrência e paralelismo. A "
            "solução responde a requisições de múltiplos clientes via TCP, garantindo "
            "sincronização das métricas com o uso de locks e delegando cálculos CPU-bound "
            "para um pool de processos.",
            body,
        )
    )

    # Introdução
    content.append(Paragraph("Introdução", styles["Heading2"]))
    content.append(
        Paragraph(
            "Aplicações distribuídas demandam coordenação cuidadosa entre componentes concorrentes. "
            "Ao combinar múltiplas threads de atendimento com um pool de processos dedicado ao "
            "cálculo de números primos, garantimos escalabilidade horizontal para o servidor e "
            "isolamento de computações intensivas. O cliente utiliza comunicação síncrona sobre "
            "TCP com mensagens JSON, mantendo um thread dedicado para recebimento das respostas.",
            body,
        )
    )

    # Metodologia
    content.append(Paragraph("Metodologia", styles["Heading2"]))
    content.append(
        Paragraph(
            "A arquitetura utiliza um servidor TCP multi-thread que aceita conexões e instancia "
            "uma thread por cliente. As requisições são decodificadas em mensagens estruturadas e "
            "encaminhadas para um componente Dispatcher que mantém estatísticas protegidas por um "
            "lock. Cada cálculo é executado por um ProcessPoolExecutor, permitindo verdadeiro "
            "paralelismo em múltiplos núcleos. A Figura 1 resume o fluxo de comunicação e "
            "cooperação entre threads e processos.",
            body,
        )
    )
    content.append(_diagram_flowable())
    content.append(Paragraph("Figura 1 – Fluxo geral da solução distribuída.", styles["BodyText"]))

    # Resultados
    content.append(Paragraph("Resultados", styles["Heading2"]))
    content.append(
        Paragraph(
            "Foram conduzidos testes funcionais por meio de múltiplos clientes simultâneos. A Tabela 1 "
            "ilustra comandos executados e respostas recebidas do servidor, comprovando o "
            "funcionamento concorrente e a manutenção de métricas em tempo real.",
            body,
        )
    )
    table_data = [
        ["Comando", "Descrição", "Resposta (resumida)"],
        ["prime 104729", "Verificação de primo grande", "{\"is_prime\": true}"],
        ["range 1 30", "Listagem de primos", "{\"count\": 10, ...}"],
        ["count 1 100000", "Contagem intensiva", "{\"count\": 9592}"],
        ["stats", "Métricas do servidor", "{\"total_requests\": 42, ...}"],
    ]
    table = Table(table_data, colWidths=[4 * cm, 6 * cm, 7 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.aliceblue]),
            ]
        )
    )
    content.append(table)

    # Conclusão
    content.append(PageBreak())
    content.append(Paragraph("Conclusão", styles["Heading2"]))
    content.append(
        Paragraph(
            "O projeto demonstra como a combinação de threads, processos e mecanismos de sincronização "
            "pode ser aplicada para construir serviços distribuídos robustos. Além de atender a múltiplos "
            "clientes simultaneamente, a solução garante paralelismo efetivo para tarefas CPU-bound, "
            "apresentando métricas claras do comportamento do sistema.",
            body,
        )
    )

    # Referências simples
    content.append(Paragraph("Referências", styles["Heading2"]))
    content.append(
        Paragraph(
            "Python Software Foundation. "
            "*Python 3 Documentation: multiprocessing — Process-based parallelism*.",
            body,
        )
    )

    doc = SimpleDocTemplate(str(destination), pagesize=A4, title="Arquitetura Distribuída")
    doc.build(content)
    return destination


if __name__ == "__main__":  # pragma: no cover
    print(f"Relatório gerado em: {generate_report()}")
