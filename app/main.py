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
    query_type = "exact"
    
    if request.method == "POST":
        query = request.form["query"]
        # selected_algorithm = request.form["algorithm"]
        limit = int(request.form.get("limit", 500))  # Default to 500
        query_type = request.form.get("query_type", "exact")
        
        print("\n========== Form Submission ==========")
        print("Running benchmark for all algorithms...")
        print(f"Query: {query}")
        print(f"Limit: {limit}")
        print(f"Query Type: {query_type}")

        if not query.strip():
            return render_template("index.html", result=None, query=query, limit=limit)
        result = {}

        # Linear
        raw_result = linear_search_streaming(dataset_path, query, limit, query_type)
        result["linear"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # Inverted Index
        raw_result = inverted_index_search(dataset_path, query, limit, query_type)
        result["inverted"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # Trie
        raw_result = trie_search(dataset_path, query, limit, query_type)
        result["trie"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        # B-Tree
        raw_result = btree_search(dataset_path, query, limit, query_type)
        result["btree"] = {
            "matches": raw_result["matches"],
            "time": raw_result["time"],
            "time_sec": round(raw_result["time"] / 1000, 4),
            "memory": raw_result["memory"]
        }

        app.config["cached_matches"] = result  # Save all matches

    return render_template("index.html", result=result, query=query, limit=limit, query_type=query_type)

@app.route("/results")
def results():
    query = request.args.get("query", "")
    limit = int(request.args.get("limit", 500))
    algorithm = request.args.get("algorithm", "linear")
    matches_dict = app.config.get("cached_matches", {})
    matches = matches_dict.get(algorithm, {}).get("matches", [])
    
    return render_template("results.html", query=query, limit=limit, matches=matches, algorithm=algorithm)

@app.route("/complexity", methods=["GET", "POST"])
def complexity():
    if request.method == "GET":
        query = request.args.get("query", "")
        query_type = request.args.get("query_type", "exact")  # <-- Add this
        return render_template(
            "complexity.html", 
            query=query,
            query_type=query_type,  # <-- Add this
            limits=[],
            chart_data={
                "linear": [],
                "inverted": [],
                "trie": [],
                "btree": []
            },
            total_time_ms=0,
            total_time_sec=0,
            total_time_min=0,
            total_time_sec_only=0
        )

    query = request.form.get("query", "")
    query_type = request.form.get("query_type", "exact")
    limits_raw = request.form.get("limits", "")
    
    if not query.strip():
        return "Please provide a valid query.", 400
    if not limits_raw.strip():
        return "Please provide dataset sizes.", 400

    try:
        limits = [int(x.strip()) for x in limits_raw.split(",") if x.strip().isdigit()]
    except Exception:
        return "Invalid input sizes. Please enter comma-separated numbers.", 400
    
    print("\n========== Running Time Complexity ==========")
    print(f"=== Query: {query}")
    print(f"=== Query Type: {query_type}")
    print(f"=== Limits: {limits}")

    algorithms = {
        "linear": linear_search_streaming,
        "inverted": inverted_index_search,
        "trie": trie_search,
        "btree": btree_search
    }

    chart_data = {algo: [] for algo in algorithms}
    start_time = time.time()

    for limit in limits:
        for algo_name, func in algorithms.items():
            try:
                result = func(dataset_path, query, limit, query_type=query_type)
                time_taken = result.get("time", 0)
                chart_data[algo_name].append(time_taken)
                print(f"{algo_name} | Limit: {limit} | Time: {time_taken} ms")
            except Exception as e:
                print(f"[ERROR] {algo_name} failed at limit {limit}: {e}")
                chart_data[algo_name].append(None)

    total_time_ms = round((time.time() - start_time) * 1000, 2)
    total_time_sec = round(total_time_ms / 1000, 2)
    total_time_min = int(total_time_sec // 60)
    total_time_sec_only = round(total_time_sec % 60, 2)

    return render_template("complexity.html", 
                           query=query, 
                           query_type=query_type,
                           limits=limits, 
                           chart_data=chart_data,
                           limits_input=limits_raw,
                           total_time_ms=total_time_ms,
                           total_time_sec=total_time_sec,
                           total_time_min=total_time_min,
                           total_time_sec_only=total_time_sec_only)


@app.route("/simulate")
def simulate():
    queries = ["funny poems", "loved this book", "boring", "interesting premise"]
    limits = [100, 500, 1000, 2000]

    algorithms = {
        "linear": linear_search_streaming,
        "inverted": inverted_index_search,
        "trie": trie_search,
        "btree": btree_search
    }

    simulation_results = []

    for query in queries:
        entry = {"query": query, "data": {}}
        for limit in limits:
            entry["data"][limit] = {}
            for algo_name, func in algorithms.items():
                try:
                    result = func(dataset_path, query, limit)
                    entry["data"][limit][algo_name] = {
                        "time": result["time"],
                        "memory": result["memory"]
                    }
                except Exception as e:
                    entry["data"][limit][algo_name] = {
                        "time": None,
                        "memory": None
                    }
                    print(f"[ERROR] {algo_name} failed on query '{query}' and limit {limit}: {e}")
        simulation_results.append(entry)

    return render_template("simulate.html", results=simulation_results)

if __name__ == "__main__":
    app.run(debug=True)