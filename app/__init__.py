from flask import Flask, redirect, url_for,render_template
import json

app = Flask(__name__)

from app import routes


