#!/usr/bin/env python3

from app import app
from apps import json_page


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5678')
