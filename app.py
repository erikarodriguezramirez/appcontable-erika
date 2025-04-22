from flask import Flask, render_template, request, send_file
from io import BytesIO
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)

TIPOS_ASIENTO = {
    "Factura autónomo con retención": [
        ("623 - Servicios profesionales", "DEBE"),
        ("4751 - Retención IRPF", "HABER"),
        ("410 - Acreedores", "HABER")
    ],
    "Factura con remanente proveedor": [
        ("600 - Compras", "DEBE"),
        ("400 - Proveedores", "HABER")
    ],
    "Remanente compensado": [
        ("400 - Proveedores", "DEBE"),
        ("555 - Pendiente de aplicación", "HABER")
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    asiento = []
    observaciones = ""
    tipo = ""
    importe = 0.0
    if request.method == 'POST':
        tipo = request.form['tipo']
        importe = float(request.form['importe'])
        observaciones = request.form['observaciones']
        estructura = TIPOS_ASIENTO.get(tipo, [])
        partes = len(estructura)
        importe_parcial = round(importe / partes, 2) if partes > 0 else 0
        asiento = [(cuenta, debehaber, importe_parcial) for cuenta, debehaber in estructura]
        if request.form.get("accion") == "PDF":
            return generar_pdf(asiento, tipo, observaciones)
        elif request.form.get("accion") == "Excel":
            return generar_excel(asiento, tipo, observaciones)
    return render_template('index.html', tipos=TIPOS_ASIENTO.keys(), asiento=asiento, tipo=tipo, observaciones=observaciones)

def generar_pdf(asiento, tipo, observaciones):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Asiento contable: {tipo}", ln=True)
    for cuenta, debehaber, importe in asiento:
        pdf.cell(200, 10, txt=f"{debehaber} | {cuenta} | {importe:.2f}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Observaciones: {observaciones}")
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="asiento.pdf", as_attachment=True)

def generar_excel(asiento, tipo, observaciones):
    df = pd.DataFrame(asiento, columns=["Cuenta", "Debe/Haber", "Importe"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Asiento", index=False)
        sheet = writer.sheets["Asiento"]
        sheet.write("E1", "Observaciones")
        sheet.write("E2", observaciones)
    output.seek(0)
    return send_file(output, download_name="asiento.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

    
