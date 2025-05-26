import os
import io
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.core.files.base import ContentFile


class InvoiceGenerator:
    """电子发票生成器"""
    
    # 注册中文字体
    @staticmethod
    def _register_chinese_fonts():
        """注册中文字体"""
        # 字体文件路径
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts')
        
        # 确保字体目录存在
        os.makedirs(font_path, exist_ok=True)
        
        # 检查是否已经有字体文件，如果没有则创建默认字体
        simsun_path = os.path.join(font_path, 'simsun.ttf')
        if not os.path.exists(simsun_path):
            # 如果没有字体文件，使用系统字体
            system_font_paths = [
                # Windows
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/simhei.ttf',
                # Linux
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
                # macOS
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/PingFang.ttc'
            ]
            
            # 尝试找到一个可用的系统字体
            font_found = False
            for system_path in system_font_paths:
                if os.path.exists(system_path):
                    try:
                        # 复制系统字体到项目目录
                        import shutil
                        shutil.copy(system_path, simsun_path)
                        font_found = True
                        break
                    except:
                        pass
            
            # 如果找不到系统字体，使用默认的Helvetica（不支持中文）
            if not font_found:
                # 无法找到中文字体，将使用默认字体
                pass
        
        # 注册字体
        try:
            if os.path.exists(simsun_path):
                pdfmetrics.registerFont(TTFont('SimSun', simsun_path))
                return True
            return False
        except:
            return False
    
    @staticmethod
    def generate_invoice_number():
        """生成发票号码"""
        # 简单模拟发票号码生成，实际可能需要更复杂的逻辑
        now = timezone.now()
        return f"FP{now.strftime('%Y%m%d%H%M%S')}{now.microsecond // 1000:03d}"
    
    @staticmethod
    def generate_pdf(invoice):
        """生成电子发票PDF
        
        Args:
            invoice: Invoice模型实例
            
        Returns:
            ContentFile: PDF文件内容
        """
        buffer = io.BytesIO()
        
        # 注册中文字体
        has_chinese_font = InvoiceGenerator._register_chinese_fonts()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # 设置样式
        styles = getSampleStyleSheet()
        
        # 如果成功注册了中文字体，则创建中文样式
        if has_chinese_font:
            # 创建使用中文字体的样式
            title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Heading1'],
                fontName='SimSun',
                fontSize=18
            )
            subtitle_style = ParagraphStyle(
                'ChineseSubtitle',
                parent=styles['Heading2'],
                fontName='SimSun',
                fontSize=14
            )
            normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName='SimSun',
                fontSize=10
            )
        else:
            # 使用默认样式
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']
        
        # 构建PDF内容
        elements = []
        
        # 标题
        elements.append(Paragraph("电子发票", title_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        # 发票信息
        elements.append(Paragraph(f"发票号码: {invoice.invoice_number}", normal_style))
        elements.append(Paragraph(f"开票日期: {invoice.invoice_date.strftime('%Y-%m-%d')}", normal_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        # 公司信息
        elements.append(Paragraph("销售方: AdWeb广告管理平台", subtitle_style))
        elements.append(Paragraph("纳税人识别号: 91XXXXXXXXXXXXXXXXXX", normal_style))
        elements.append(Paragraph("地址: 北京市海淀区中关村大街1号", normal_style))
        elements.append(Paragraph("电话: 010-12345678", normal_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        # 购买方信息
        elements.append(Paragraph("购买方:", subtitle_style))
        elements.append(Paragraph(f"名称: {invoice.title}", normal_style))
        elements.append(Paragraph(f"纳税人识别号: {invoice.tax_number}", normal_style))
        if invoice.address:
            elements.append(Paragraph(f"地址: {invoice.address}", normal_style))
        if invoice.contact_phone:
            elements.append(Paragraph(f"电话: {invoice.contact_phone}", normal_style))
        elements.append(Spacer(1, 1 * cm))
        
        # 发票明细表格
        invoice_items = invoice.items.all().select_related('transaction')
        data = [
            ['序号', '项目名称', '规格型号', '单位', '数量', '单价', '金额', '税率', '税额'],
        ]
        
        total_amount = Decimal('0.00')
        
        # 如果没有明细项，则添加一个总金额项
        if not invoice_items.exists():
            amount = invoice.amount
            tax_rate = Decimal('0.06')  # 假设6%增值税率
            tax = amount * tax_rate
            total_amount = amount
            
            data.append([
                1,
                invoice.content,
                '-',
                '项',
                '1',
                f"{amount:.2f}",
                f"{amount:.2f}",
                '6%',
                f"{tax:.2f}"
            ])
        else:
            # 有明细项，则逐项添加
            for i, item in enumerate(invoice_items, 1):
                amount = item.amount
                tax_rate = Decimal('0.06')  # 假设6%增值税率
                tax = amount * tax_rate
                total_amount += amount
                
                data.append([
                    i,
                    invoice.content,
                    '-',
                    '项',
                    '1',
                    f"{amount:.2f}",
                    f"{amount:.2f}",
                    '6%',
                    f"{tax:.2f}"
                ])
        
        # 添加合计行
        tax_total = total_amount * Decimal('0.06')
        data.append(['合计', '', '', '', '', '', f"{total_amount:.2f}", '', f"{tax_total:.2f}"])
        
        # 创建表格
        table = Table(data, colWidths=[0.5*cm, 3*cm, 2*cm, 1*cm, 1*cm, 2*cm, 2*cm, 1*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            # 设置表头字体
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold' if not has_chinese_font else 'SimSun'),
            # 设置所有单元格字体
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica' if not has_chinese_font else 'SimSun'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1 * cm))
        
        # 价税合计
        price_tax_total = total_amount + tax_total
        elements.append(Paragraph(f"价税合计: {price_tax_total:.2f} 元", subtitle_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        # 备注
        if invoice.remark:
            elements.append(Paragraph(f"备注: {invoice.remark}", normal_style))
            elements.append(Spacer(1, 0.5 * cm))
        
        # 底部信息
        elements.append(Paragraph("本发票为电子发票，与纸质发票具有同等法律效力。", normal_style))
        elements.append(Paragraph(f"开票日期: {invoice.invoice_date.strftime('%Y-%m-%d')}", normal_style))
        elements.append(Paragraph(f"打印日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        
        # 构建PDF
        doc.build(elements)
        
        # 获取PDF内容
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # 生成文件名
        filename = f"invoice_{invoice.invoice_number}.pdf"
        
        # 返回ContentFile对象
        return ContentFile(pdf_content, name=filename) 