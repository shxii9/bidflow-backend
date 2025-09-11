import pytest
import json
from app import app, db, User

# -----------------------------------------------------------------------------
# 1. إعداد بيئة الاختبار (Test Fixture)
# -----------------------------------------------------------------------------
@pytest.fixture(scope='module')
def test_client():
    # ضبط التطبيق لوضع الاختبار
    app.config.update({
        "TESTING": True,
        # استخدام قاعدة بيانات في الذاكرة للاختبارات (سريعة ونظيفة)
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        # تعطيل CSRF في النماذج (إذا كنت تستخدمها)
        "WTF_CSRF_ENABLED": False
    })

    with app.test_client() as testing_client:
        # إنشاء سياق التطبيق
        with app.app_context():
            # إنشاء جميع جداول قاعدة البيانات
            db.create_all()
            yield testing_client  # هنا يتم تشغيل الاختبارات
            # بعد انتهاء الاختبارات، يتم حذف كل شيء
            db.drop_all()

# -----------------------------------------------------------------------------
# 2. كتابة دالة الاختبار (The Test Function)
# -----------------------------------------------------------------------------
def test_registration_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/register' endpoint is posted to (POST) with valid data
    THEN check that the response is valid and the user is created
    """
    # بيانات مستخدم جديد وهمي
    new_user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }

    # إرسال طلب POST إلى نقطة النهاية
    response = test_client.post('/api/register',
                                data=json.dumps(new_user_data),
                                content_type='application/json')

    # --- التأكيدات (Assertions) ---
    # 1. التأكد من أن رمز الحالة هو 201 (Created)
    assert response.status_code == 201

    # 2. التأكد من أن الرسالة صحيحة
    response_data = json.loads(response.data)
    assert "تم تسجيل المستخدم بنجاح!" in response_data['message']
    assert response_data['user']['username'] == "testuser"

    # 3. (اختياري ولكن مهم) التأكد من أن المستخدم تم إنشاؤه بالفعل في قاعدة البيانات
    user = User.query.filter_by(username="testuser").first()
    assert user is not None
    assert user.email == "test@example.com"

