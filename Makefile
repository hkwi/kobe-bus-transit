www.city.kobe.lg.jp:
	wget -r -np http://www.city.kobe.lg.jp/life/access/transport/bus/index.html -A "[0-9]*.html"
	git add www.city.kobe.lg.jp/life/access/transport/bus/jikoku/basjikoku/[0-9]*.html
	git commit -m "import" www.city.kobe.lg.jp/life/access/transport/bus/jikoku/basjikoku/[0-9]*.html
