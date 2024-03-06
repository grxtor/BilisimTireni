from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "ahe14efdaw"

# MySQL bağlantısı
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="ahe14efdaw",
  database="deneme"
)
mycursor = mydb.cursor(buffered=True)

@app.route('/')
def mainpage1():
    return render_template('index.html')

@app.route('/balon-oyunu')
def mouse():
    return render_template('oyunlar/mouse.html') 

@app.route('/klavye')
def klavye():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/klavye.html', student_info=student_info)
    return redirect('/student_login')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        # Kullanıcı zaten oturum açmış, direkt olarak dashboard'a yönlendir
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mycursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = mycursor.fetchone()
        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return "Kullanıcı adı veya şifre yanlış"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:  # Assuming you have user authentication
        # Fetch class names from the database
        mycursor.execute("SELECT * FROM classes")  # 'classes' tablonuzdaki tüm sınıfları çeker
        siniflar = mycursor.fetchall()
        return render_template('öğretmen/dashboard.html', siniflar=siniflar)
    else:
        return redirect('/login')  # Or your login page route

@app.route('/logout-students')
def logout_students():
    if 'student_info' in session:
            session.pop('student_info', None)
            return redirect('/student_login')
    if 'username' in session:
            session.pop('username', None)
            return redirect('/login')

@app.route('/logout')
def logout():
    if 'username' in session:
            session.pop('username', None)
            return redirect('/login')
    if 'student_info' in session:
            logout_students()

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        tc_no = request.form['tc_no']
        parent_phone = request.form['parent_phone']
        student_no = request.form['student_no']
        student_name = request.form['student_name']
        class_name = request.form['class_name']

        try:
            mycursor.execute("INSERT INTO students (tc_no, parent_phone, student_no, student_name, class_name) VALUES (%s, %s, %s, %s, %s)", (tc_no, parent_phone, student_no, student_name, class_name))
            mydb.commit()
            return redirect('/some_success_page')
        except mysql.connector.errors.IntegrityError as e:
            # Here you handle the integrity error
            # For example, you could return to the student addition page with an error message
            print("Error: Could not add student. Please make sure the class exists.")
            return render_template('add_student.html', error="Could not add student. Please make sure the class exists.")
    else:
        return render_template('öğretmen/add_student.html')

@app.route('/class/<class_name>')
def class_students(class_name):
    if 'username' in session:
        mycursor.execute("SELECT * FROM students WHERE class_name = %s", (class_name,))
        students = mycursor.fetchall()
        return render_template('öğretmen/class_students.html', students=students, class_name=class_name)

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'username' in session:
        if request.method == 'POST':
            return redirect('/dashboard')
        mycursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = mycursor.fetchone()
        return render_template('öğretmen/edit_student.html', student=student)
    return redirect('/login')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if 'student_info' in session:
        return redirect('/student_dashboard')
    if request.method == 'POST':
        tc_no = request.form['tc_no']
        student_no = request.form['student_no']
        mycursor.execute("SELECT * FROM students WHERE tc_no = %s AND student_no = %s", (tc_no, student_no))
        student = mycursor.fetchone()
        if student:
            session['student_info'] = {
                'student_id': student[0],  # Assuming student_id is the first column
                'tc_no': tc_no,
                'student_no': student_no,
                'student_name': student[5],
                'class_name': student[7],  # Adjust according to your actual table structure
                'new_points': student[8],
                'disability': student[9],
                'yapboz1': student[11],
                'cinsiyet': student[13]  
            }
            return redirect('/student_dashboard')
            print(session)
        else:
            return "TC Kimlik No veya Öğrenci No yanlış"
    return render_template('student_login.html')

@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('student_dashboard.html', student_info=student_info)
    else:
        return "Öğrenci bilgileri alınamadı."
    
@app.route('/get_student_info')
def get_student_info():
    if 'student_info' in session:
        tc_no = session['student_info']['tc_no']
        student_no = session['student_info']['student_no']
        # Öğrencinin güncel bilgilerini veritabanından çek
        mycursor.execute("SELECT student_name, new_points, disability FROM students WHERE tc_no = %s AND student_no = %s", (tc_no, student_no))
        student_info = mycursor.fetchone()
        if student_info:
            # Bilgileri JSON formatında döndür
            return jsonify({
                'student_name': student_info[0],
                'new_points': student_info[1],
                'disability': student_info[2]
            })
        else:
            return jsonify({'error': 'Öğrenci bilgisi bulunamadı'}), 404
    else:
        return jsonify({'error': 'Oturum bilgisi bulunamadı'}), 401

@app.route('/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    try:
        # 'iduser' sütunu kullanarak öğrenciyi sil
        query = "DELETE FROM students WHERE iduser = %s"
        mycursor.execute(query, (student_id,))
        mydb.commit()
        return redirect('students_list')
    except mysql.connector.Error as err:
        return f"Veritabanı hatası: {err}"

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if 'username' in session:
        if request.method == 'POST':
            class_name = request.form['class_name']
            mycursor.execute("SELECT * FROM classes WHERE class_name = %s", (class_name,))
            existing_class = mycursor.fetchone()
            if existing_class:
                # Sınıf zaten varsa bir hata mesajı göster
                return "Bu sınıf adı zaten mevcut. Lütfen farklı bir ad girin."
            class_description = request.form['class_description']
            teacher_name = session['username']
            mycursor.execute("INSERT INTO classes (class_name, description, teacher_name) VALUES (%s, %s, %s)", (class_name, class_description, teacher_name))
            mydb.commit()
            return redirect('/dashboard')
        return render_template('öğretmen/add_classes.html')
    return redirect('/add_classes')

@app.route('/get_student_progress')
def get_student_progress():
    if 'student_info' in session:
        student_id = session['student_info']['student_no']
        # Öğrencinin test ilerlemelerini çek
        mycursor.execute("SELECT test_name, completion_percentage FROM student_test_progress WHERE student_id = %s", (student_id,))
        progress_data = mycursor.fetchall()
        progress_info = [{'test_name': row[0], 'completion_percentage': row[1]} for row in progress_data]
        return jsonify(progress_info)
    else:
        return jsonify({'error': 'Öğrenci bilgileri alınamadı.'}), 401

@app.route('/complete_yapboz1', methods=['POST'])
def complete_yapboz1():
    # Session'dan öğrenci bilgilerini al
    if 'student_info' in session:
        student_id = session['student_info']['student_id']
        
        # Öğrencinin yapboz oyununu tamamladığını güncelle
        try:
            query = "UPDATE students SET yapboz1 = TRUE WHERE student_id = %s"
            mycursor.execute(query, (student_id,))
            mydb.commit()
            
            return jsonify({'success': True, 'message': 'Yapboz başarıyla tamamlandı olarak işaretlendi.'})
        except mysql.connector.Error as err:
            return jsonify({'success': False, 'message': 'Veritabanı hatası: {}'.format(err)})
    else:
        return jsonify({'success': False, 'message': 'Oturum bilgisi bulunamadı.'}), 401

@app.route('/submit_score', methods=['POST'])
def submit_score():
    if 'student_info' in session:
        # JSON isteğinden skoru al
        data = request.get_json()
        new_score = data['score']
        
        # Oturumdan öğrenci bilgilerini al
        student_info = session['student_info']
        tc_no = student_info['tc_no']
        student_no = student_info['student_no']

        # students tablosundaki new_points değerini güncelle
        update_query = """
        UPDATE students
        SET new_points = %s
        WHERE tc_no = %s AND student_no = %s
        """
        mycursor.execute(update_query, (new_score, tc_no, student_no))
        mydb.commit()

        # Başarılı yanıt döndür
        return jsonify({'success': True, 'message': 'Skor başarıyla güncellendi.'})
    else:
        # Kullanıcı oturum açmamışsa hata döndür
        return jsonify({'success': False, 'message': 'Kullanıcı girişi yapılmamış.'}), 401

@app.route('/oyunlar')
def oyunlar():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/oyunlar.html', student_info=student_info)
    return redirect('/student_login')

@app.route('/oyunlar/eslestirme/donanım-eşleştirme')
def test2():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/donanimyerlestirme.html', student_info=student_info)
    return redirect('/student_login')

@app.route('/oyunlar/Giriş-Çıkış-Elemanları')
def giriscikisoyunu():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/Giriş Çıkış Elemanları.html', student_info=student_info)
    return redirect('/student_login')

@app.route('/oyunlar/YapBoz/icdıs')
def yapboz2():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/YapBoz2icdis.html', student_info=student_info)
    return redirect('/student_login')


@app.route('/ilktest')
def ilktest():
    return render_template('testler/ilktest.html')

@app.route('/oyunlar/YapBoz/Donanımİsimleri')
def yapboz():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/yapboz.html', student_info=student_info)
    return redirect('/student_login')

@app.route('/ders/ders1')
def ders1():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('ilkders.html', student_info=student_info)
    return redirect('/student_login')

@app.route('/oyunlar/balon')
def balonpatlatma():
    if 'student_info' in session:
        student_info = session['student_info']
        return render_template('oyunlar/mouse.html', student_info=student_info)
    return redirect('/student_login')


@app.route('/get_yapboz1_status')
def get_yapboz1_status():
    if 'student_info' not in session:
        return jsonify({'error': 'Oturum bilgisi bulunamadı'}), 401
    
    student_id = session['student_info']['student_id']
    cursor = mydb.commit()

    query = """
    SELECT yapboz1
    FROM students
    WHERE student_id = %s
    """
    cursor.execute(query, (student_id,))
    yapboz1_status = cursor.fetchone()

    if yapboz1_status:
        return jsonify({'yapboz1_status': yapboz1_status[0]})
    else:
        return jsonify({'error': 'Öğrenci bilgisi bulunamadı.'}), 404
    
if __name__ == '__main__':
    app.run(debug=True)



