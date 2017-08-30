import csv
import lxml.etree
import glob
import re
import os.path
import html_table

def to_text(cell):
	txt = lxml.etree.tostring(cell, encoding="UTF-8", method="text").decode("UTF-8")
	return txt.replace("　"," ").strip()

def headers(li):
	assert li[0] == "神戸市バス　時刻表"
	route = re.match(r"^(?P<number>\d+)系統[　\s]+(?P<name>.+) 行き$", li[1])
	assert route, repr(li[1])
	dep = re.match(r"^(?P<dep>.+)　発$", li[2])
	assert dep, repr(li[2])
	assert li[3] in ("平日", "土曜日", "日曜日・祝日"), li[3]
	assert not li[4]
	assert not li[5]
	return list(route.groups() + dep.groups() + (li[3],))

def note_split(bulk):
	notes = []
	while bulk:
		m = re.match("^(・.{2}[^\n・]*)", bulk)
		assert m
		note = m.group(1)
		notes.append(note)
		bulk = bulk[len(note):].strip()
	
	return notes

stop_times = [tuple("ファイル名 系統 行き 発 曜日 時 分 備考欄 印 備考".split())]
notes = [tuple("ファイル名 備考欄 備考".split())]

def proc(f):
	bn = os.path.basename(f)
	t = lxml.etree.HTML(open(f, "rb").read())
	h = [None]*6 # h1 to h6
	note = 0
	info = {}
	for n in t.xpath(".//*"):
		try:
			i = ("h1","h2","h3","h4","h5","h6").index(n.tag)
			if n.text:
				h[i] = n.text.strip()
			else:
				h[i] = None
		except ValueError:
			if n.tag != "table":
				continue
			
			hs = "".join([c for c in h if isinstance(c, str)])
			if not hs:
				continue
			
			tb = html_table.Table(n).matrix(to_text)
			for r in tb:
				assert len(r) == 2, f
				
				r[1] = r[1].replace("\u25cb","\u3007")
				
				if r[0] == "備考":
					info = {}
					note += 1
					
					for i in note_split(r[1]):
						notes.append([bn, "備考%d" % note, i])
						m = re.match(r"^・([\u203b\u25a0-\u26ff\u3007山新直])印?[はの](.*)$", i)
						if m:
							k, v = m.groups()
							info[k] = v
						
						m = re.match(r"^・▲・△印は(.*)（△印は(.*)）", i)
						if m:
							a, b = m.groups()
							info["▲"] = a
							info["△"] = "%s（%s）" % (a, b)
				else:
					assert r[0][-1] == "時"
					hour = r[0][:-1]
					assert int(hour) > 0 # GTFS requires 25:00:00
					for m in r[1].split():
						minute, memo = m.split("分", 1)
						int(minute)
						
						memo_li = []
						if memo:
							try:
								memo_li = [info[x] for x in memo]
							except:
								print(f, memo, note, info)
								raise
						elif "無" in info:
							memo_li = [info["無"]]
						
						stop_times.append([bn]+headers(h)+[
							hour, minute, "備考%d" % note, memo, ";".join(memo_li)])
						

for r in glob.glob("www.city.kobe.lg.jp/life/access/transport/bus/jikoku/basjikoku/[0123456789]*.html"):
	proc(r)

csv.writer(open("parsed_stop_times.csv","w")).writerows(stop_times)
csv.writer(open("parsed_notes.csv","w")).writerows(notes)
