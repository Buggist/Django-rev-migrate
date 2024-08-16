# Python 3.12

import ast
import importlib.util
import re
import os

import pymysql

#============================================================
# 模型层文件名
file_path = r'C:\Django_Projects\kggroup\sellcard\models.py'

# 数据库连接参数
db_config = {
	'host': '192.168.250.18',
	'user': 'kggroup',
	'password': 'kggroup123465',
	'db': 'kggroup',
}

# 模型配置
managed = True

#============================================================

def get_tablenamelist_from_model(file_path):
	# 读取文件内容
	with open(file_path, 'r', encoding='utf-8') as file:
		file_content = file.read()

	# 解析文件内容为AST（抽象语法树）
	parsed_content = ast.parse(file_content)

	# 用于存储db_table值的列表
	db_tables = []

	# 遍历AST节点，寻找类定义和Meta类定义
	for node in ast.walk(parsed_content):
		#print(node)
		# 检查是否为类定义节点
		if isinstance(node, ast.ClassDef):
			# 检查类名是否为'Model'
			for subnode in node.body:
				# 检查是否为类定义节点（即内部类，即Meta类）
				if isinstance(subnode, ast.ClassDef) and subnode.name == 'Meta':
					# 遍历Meta类体中的节点
					for meta_subnode in subnode.body:
						# 检查是否为属性赋值节点，并且属性名为'db_table'
						if isinstance(meta_subnode, ast.Assign) and \
							isinstance(meta_subnode.targets[0], ast.Name) and \
							meta_subnode.targets[0].id == 'db_table':
							# 获取'db_table'属性的值
							db_table_value = meta_subnode.value.value
							# 将值添加到列表中
							db_tables.append(db_table_value)
	return set(db_tables)


def get_tablenamelist_from_database(db_config):
	# 建立数据库连接
	connection = pymysql.connect(**db_config)
	 
	try:
		# 创建游标对象
		with connection.cursor() as cursor:
			# 查询所有表名称的SQL语句
			sql = "SHOW TABLES"
			
			# 执行SQL查询
			cursor.execute(sql)
			
			# 获取查询结果
			result = cursor.fetchall()
			
			# 提取表名并保存到列表中
			table_names = [table[0] for table in result]
	 
	except pymysql.MySQLError as e:
		print(f"Error: {e}")
	 
	finally:
		# 关闭数据库连接
		connection.close()
		
	return set(table_names)
	

def to_camel_case(text):
       # 将下划线分隔的字符串转换为驼峰命名法
       return re.sub(r'(?:^|_)([a-zA-Z])', lambda m: m.group(1).upper(), text)


def map_field_type(mysql_type):
   # 简单地将MySQL数据类型映射到Django字段类型
   if mysql_type.startswith('int'):
       return 'models.IntegerField'
   elif mysql_type.startswith('varchar'):
       length = mysql_type.split('(')[1].rstrip(')')
       return f'models.CharField(max_length={length})'
   elif mysql_type == 'datetime':
       return 'models.DateTimeField'
   elif mysql_type == 'date':
       return 'models.DateField'
   elif mysql_type == 'text':
       return 'models.TextField'
   elif mysql_type.startswith('decimal'):
       # 假设 decimal(10,2) 形式
       digits, places = mysql_type.split('(')[1].rstrip(')').split(',')
       return f'models.DecimalField(max_digits={digits}, decimal_places={places})'
   # 这里可以添加更多的类型映射
   else:
       return 'models.CharField'  # 默认使用CharField
 
 
def execute_modelcreate(db_config, table_names, file_path, managed):
	# 连接到数据库
	connection = pymysql.connect(**db_config)
	
	model_str_list = []
	 
	try:
	   with connection.cursor() as cursor:
		   for table_name in table_names:
			   cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
			   columns = cursor.fetchall()
			   
			   # 将表名转换为驼峰命名法作为类名
			   class_name = to_camel_case(table_name)
		 
			   model_str = f"class {class_name}(models.Model):\n"
			   
			   for column in columns:
				   field_name, field_type, null, key, default, extra = column
				   django_field = map_field_type(field_type)
		 
				   if key == 'PRI':
					   django_field = 'models.AutoField(primary_key=True)'
		 
				   model_str += f"    {field_name} = {django_field}"
				   if default:
					   model_str += f" default={default}"
				   model_str += "\n"
		 
			   model_str += "\n    class Meta:\n"
			   model_str += f"        managed = {str(managed)}\n"
			   model_str += f"        db_table = \"{table_name}\"\n"
			   
			   model_str_list.append(model_str)
		   
	except Exception as e:
		print(e)
	 
	finally:
	   connection.close()
	   
	with open(file_path, 'a', encoding="utf-8-sig") as file:
		for model_str in model_str_list:
			file.writelines("\n\n")
			file.writelines(model_str)
			file.writelines("\n")
	
	
if __name__ == "__main__":
	tables_model = get_tablenamelist_from_model(file_path)					
	tables_database = get_tablenamelist_from_database(db_config)

	tables_new = tables_database - tables_model

	#=========================================
	for item in tables_new:
		print("新增表模型: ", item)

	print("==================================")
	print("总共新增表模型数量：", len(tables_new))
	print("==================================")
	os.system("pause")
	#=========================================

	execute_modelcreate(db_config, tables_new, file_path, managed)
	
	print("================反向迁移完成================")
	os.system("pause")











