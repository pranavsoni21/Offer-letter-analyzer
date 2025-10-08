from flask import Flask, request, jsonify, render_template
from recommendation_logic import analyze_offer

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    ctc = float(request.form.get('ctc'))
    deductions = float(request.form.get('deductions'))
    notice_period = int(request.form.get('notice_period'))
    benefits = request.form.getlist('benefits')
    job_title = request.form.get('job_title')
    location = request.form.get('location')

    result = analyze_offer(ctc, deductions, notice_period, benefits, job_title, location)

    return render_template('result.html',
                           result=result,
                           job_title=job_title,
                           location=location,
                           ctc=ctc,
                           deductions=deductions,
                           notice_period=notice_period,
                           benefits=benefits)


if __name__ == "__main__":
    app.run(debug=True)
