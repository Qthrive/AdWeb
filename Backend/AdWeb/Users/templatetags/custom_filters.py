from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """为表单字段添加 CSS 类"""
    return field.as_widget(attrs={"class": css_class})