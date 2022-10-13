import fitz
import pandas as pd


img_path = 'C:/Users/admin/Desktop/B22106980137_附件/可视化结果/数据集B5/'
doc = fitz.open()

# 循环path中的文件，可import os 然后用 for img in os.listdir(img_path)实现
# 这里为了让文件以1，2，3的形式进行拼接，就偷懒循环文件名中的数字。
path1 = './result/' + '数据集' + 'B' + str(5)
path = path1 + '/data_0.6997202136555108.csv'
dict = {
	'Unnamed: 0': [],
	'batch_index': [],
	'item_material': [],
	'flat_index': [],
	'item_id': [],
	'x': [],
	'y': [],
	'x_length': [],
	'y_length': []
}

print('读取文件路径为: ', path)
data = pd.read_csv(path)
data_dict = data.to_dict('list')
for key in data_dict.keys():
	dict[key].extend(data_dict[key])
for b in range(dict['batch_index'][-1] + 1):
	index = []
	for i in range(len(dict['y'])):
		if dict['batch_index'][i] == b:
			index.append(i)
	num_patterns = dict['flat_index'][index[-1]] + 1
	print(num_patterns)
	for j in range(num_patterns):
		img_file = img_path + '/batch' + str(b) + 'flat' + str(j) + '.jpg'
		# img = str(i) + '.jpg'
		# img_file = img_path + '/' + img
		imgdoc = fitz.open(img_file)
		pdfbytes = imgdoc.convertToPDF()
		pdf_name = 'batch' + str(b) + 'flat' + str(j) + '.pdf'
		imgpdf = fitz.open(pdf_name, pdfbytes)
		doc.insertPDF(imgpdf)
doc.save('combined.pdf')
doc.close()
