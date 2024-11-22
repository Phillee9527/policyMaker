def generate_markdown(insurance_data, selected_clauses):
    markdown = f"""# 投保人
名称：{insurance_data['policyholder']}

# 被保险人
名称：{insurance_data['insured']['name']}
证件类型：{insurance_data['insured']['id_type']} 证件号码：{insurance_data['insured']['id_number']}
联系人：{insurance_data['insured']['contact']['name']} 联系人电话：{insurance_data['insured']['contact']['phone']} 联系人邮箱：{insurance_data['insured']['contact']['email']}
联系地址：{insurance_data['insured']['contact']['address']} 联系邮编：{insurance_data['insured']['contact']['postal_code']}

# 被保险人标的地址
名称：{insurance_data['property']['name']}
地址：{insurance_data['property']['address']}

# 主险
## 第一部分 物质损失
"""
    
    # 添加物质损失表格
    markdown += "\n| 标的类别 | 保险金额（元） | 费率（%） | 保费（元） |\n"
    markdown += "|----------|--------------|---------|----------|\n"
    for item in insurance_data['material_loss']:
        markdown += f"| {item['标的类别']} | {item['保险金额（元）']} | {item['费率（%）']} | {item['保费（元）']} |\n"
    
    # 添加特别约定
    markdown += "\n# 特别约定\n\n"
    for i, clause in enumerate(selected_clauses, 1):
        markdown += f"{i}. {clause['扩展条款正文']}\n"
    
    return markdown 