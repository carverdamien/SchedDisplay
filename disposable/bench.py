import smv.DataDict as DataDict
import smv.LinesFrame as LinesFrame
from smv.VarsViewController import VarsViewController
import pandas as pd
import json

def main():
	var = VarsViewController()
	path = "./examples/trace/mysql.tar"
	config = var.parse(json.load(open("./examples/line/dummy.json", "r")))
	only = config['input']
	dd = DataDict.from_tar(path, only)
	df = pd.DataFrame(dd)
	lf = LinesFrame.from_df(df, config)
	pass

if __name__ == '__main__':
	main()
