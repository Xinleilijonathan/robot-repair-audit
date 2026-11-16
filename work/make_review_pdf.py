from pathlib import Path
import re, html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
root=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
styles['BodyText'].fontName='Times-Roman'
styles['BodyText'].fontSize=10.5
styles['BodyText'].leading=14
styles['BodyText'].spaceAfter=7
def clean(s):
    s=s.replace('–','-').replace('—','-').replace('’',"'").replace('“','"').replace('”','"')
    s=re.sub(r'\\\((.*?)\\\)',lambda m:m[1],s)
    for a,b in [(r'\in',' in '),(r'\sim',' ~ '),(r'\Pr','Pr'),(r'\qquad','; '),(r'\{','{'),(r'\}','}'),(r'\,',' '),(r'\[',''),(r'\]','')]: s=s.replace(a,b)
    s=html.escape(s)
    s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\*(.*?)\*',r'<i>\1</i>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#235b88">\1</link>',s)
    return s
story=[]
for block in (root/'outputs/initial_paper.md').read_text(encoding='utf-8').split('\n\n'):
    block=block.strip()
    if not block: continue
    if block.startswith('|'):
        story.append(Paragraph('Result table: all four conditions are NOT RUN. Admission counts, target gains, old-success losses, net changes, and rollout costs remain to be measured.',styles['BodyText']))
        continue
    style='BodyText'
    if block.startswith('# '): style='Title'; block=block[2:]
    elif block.startswith('## '): style='Heading2'; block=block[3:]
    elif block.startswith('### '): style='Heading3'; block=block[4:]
    story.append(Paragraph(clean(block).replace('\n','<br/>'),styles[style]))
def footer(c,d):
    c.setFont('Helvetica',8); c.setFillColor(colors.HexColor('#586372'))
    c.drawString(48,27,'PRE-EXPERIMENT REVIEW DRAFT | November 15, 2026')
    c.drawRightString(564,27,str(d.page))
doc=SimpleDocTemplate(str(root/'outputs/initial_paper.pdf'),leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=45)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
