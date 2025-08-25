from flask import Flask, render_template
app = Flask(__name__, static_url_path='/static', static_folder='./static', template_folder='./templates')

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/home')
@needs_login
def hello_world():
    return 'Hello World'

if __name__ == '__main__':
    app.run()
