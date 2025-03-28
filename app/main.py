from flask import Flask, request, render_template
from search_algorithms.linear_search import linear_search_streaming
from search_algorithms.inverted_index_search import inverted_index_search
from search_algorithms.trie_search import trie_search
from search_algorithms.btree_search import btree_search
import json
import time
import tracemalloc

app = Flask(__name__)
dataset_path = "dataset/Books_5-core.json"

@app.route("/", methods=["GET", "POST"])
def index():
    result = {}
    query = ""
    selected_algorithm = ""
    limit = 500
    
    if request.method == "POST":
        query = request.form["query"]
        # selected_algorithm = request.form["algorithm"]
        limit = int(request.form.get("limit", 500))  # Default to 500
        
        print("\n========== Form Submission ==========")
        print("Running benchmark for all algorithms...")
        print(f"Query: {query}")
        print(f"Limit: {limit}")
        
        if not query.strip():
            return render_template("index.html", result=None, query=query, limit=limit)
        result = {}

        # Linear
        raw_result = linear_search_streaming(dataset_path, query, limit)
        result["linear"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # Inverted Index
        raw_result = inverted_index_search(dataset_path, query, limit)
        result["inverted"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # Trie
        raw_result = trie_search(dataset_path, query, limit)
        result["trie"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # B-Tree
        raw_result = btree_search(dataset_path, query, limit)
        result["btree"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        app.config["cached_matches"] = result  # Save all matches

    return render_template("index.html", result=result, query=query, limit=limit)

@app.route("/results")
def results():
    query = request.args.get("query", "")
    limit = int(request.args.get("limit", 500))
    algorithm = request.args.get("algorithm", "linear")
    matches_dict = app.config.get("cached_matches", {})
    matches = matches_dict.get(algorithm, {}).get("matches", [])
    
    return render_template("results.html", query=query, limit=limit, matches=matches, algorithm=algorithm)

if __name__ == "__main__":
    app.run(debug=True)