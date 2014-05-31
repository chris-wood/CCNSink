from flask import Flask, request, Response
app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def echo():
    return request.args.get('nonce', '')
 
if __name__ == "__main__":
    app.run()