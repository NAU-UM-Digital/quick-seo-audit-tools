from ..seo_tools.helpers import database as db
from datetime import datetime
from flask import Flask
from flask import request
from flask import render_template



app = Flask(__name__)
db_path = f'../test_folder/2024-08-14_crawl-database.db' # TODO:EXPAND ON DB SELECTION LOGIC 
db.init_output_db(db_path)

@app.route("/")
def hello_world():
    network_analysis_data = db.list_network_analysis_values()
    list = ''.join([f"<tr><th>{i[1]}</th><th>{i[2]}</th><th><a href='/inspect-url?url={i[0]}'>{i[0]}</a></th><th>{i[3]}</th></tr>" for i in db.list_distinct_requests()])
    return f'<h1>Site exploration dashboard</h1><table>{list}</table>'

@app.route("/inspect-url")
def inspect_url():
    list = [i[0] for i in db.list_distinct_requests()]
    url_to_inspect = request.args.get('url', '')
    if url_to_inspect and url_to_inspect in list:
        return render_template('inspect-url.html',
                               page_data=db.show_page_data(url_to_inspect),
                               in_links=db.return_ranked_in_links(url_to_inspect),
                               canonicalized_urls=db.return_canonicalized_urls(url_to_inspect)
        )
    elif url_to_inspect == "":
        return "<p>No url was provided.</p>"
    else:
        return "<p>This url does not exist</p>"

@app.route("/new-crawl")
def new_crawl_form():
    return f"<p>This hasn't been build yet</p>"
