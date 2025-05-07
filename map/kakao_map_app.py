from flask import Flask

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from map.kakao_map import kakao_map

app = Flask(__name__)
app.register_blueprint(kakao_map)

if __name__ == '__main__':
    app.run(debug=True) 