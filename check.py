from executioner.commands.parser.excel_parser import parse_excel

xlsx_path = r"C:\Users\rasan\Desktop\work\Book1.xlsx"
content = parse_excel(xlsx_path)
print(content)
