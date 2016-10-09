from flask import Flask
import pigpio

app = Flask(__name__)
pi = pigpio.pi()


@app.route('/left')
def turn_left():
    pi.set_servo_pulsewidth(18, 500)
    return 'Turned left'


@app.route('/right')
def turn_right():
    pi.set_servo_pulsewidth(18, 2500)
    return 'Turned right'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
