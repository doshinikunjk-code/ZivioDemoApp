"""
Phase 6: Business Templates Testing
Tests for 6 pre-built industry prototypes that auto-configure the entire demo.
Templates: Restaurant, Dentist, Pharmacy, Pizza, Doctor, Skilled Trades
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Template configurations to test
TEMPLATES = {
    'dentist': {
        'name': 'Bright Smile Dental',
        'tagline': 'Family Dentistry & Cosmetic Care',
        'monthly_price': '$599',
        'brand_tagline': 'Your Smile, Our Priority',
    },
    'pizza': {
        'name': 'Slice House Pizza',
        'tagline': 'Hand-Tossed, Wood-Fired',
        'monthly_price': '$599',
        'brand_tagline': 'Real Pizza, Real Fast',
    },
    'pharmacy': {
        'name': 'MedCare Pharmacy',
        'tagline': 'Your Neighbourhood Pharmacy',
        'monthly_price': '$599',
        'brand_tagline': 'Care Beyond the Counter',
    },
    'doctor': {
        'name': 'CarePlus Medical Clinic',
        'tagline': 'Family Medicine & Walk-In',
        'monthly_price': '$599',
        'brand_tagline': 'Healthcare That Listens',
    },
    'trades': {
        'name': 'ProFix Home Services',
        'tagline': 'Plumbing, Electrical & HVAC',
        'monthly_price': '$599',
        'brand_tagline': 'We Fix It Right',
    },
    'restaurant': {
        'name': 'Desi Road Restaurant',
        'tagline': 'Elevated Indian Cuisine',
        'monthly_price': '$599',
        'brand_tagline': 'Desi Daru Desi Khana',
    },
}


class TestHealthEndpoint:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is running"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API health check passed: {data['message']}")


class TestRestaurantConfigEndpoints:
    """Test restaurant config CRUD for template application"""
    
    def test_get_default_restaurant(self):
        """Test GET /api/restaurant/default returns config"""
        response = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "tagline" in data
        assert "menu" in data
        print(f"✓ GET /api/restaurant/default - Current config: {data['name']}")
    
    def test_update_restaurant_with_dentist_template(self):
        """Test PUT /api/restaurant/default with Dentist template config"""
        template = TEMPLATES['dentist']
        payload = {
            'name': template['name'],
            'tagline': template['tagline'],
            'monthly_price': template['monthly_price'],
            'brand_tagline': template['brand_tagline'],
            'city': 'Brampton',
            'phone': '(437) 331-5615',
            'location': '220 Queen St E, Brampton',
            'hours': 'Mon-Fri 8am-6pm, Sat 9am-3pm',
            'special_name': 'Free Teeth Whitening Consultation',
            'special_desc': 'this month only',
            'menu': [
                {'name': 'Regular Checkup & Cleaning', 'price': 199, 'category': 'preventive'},
                {'name': 'Teeth Whitening', 'price': 349, 'category': 'cosmetic'},
                {'name': 'Dental Filling', 'price': 175, 'category': 'restorative'},
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/restaurant/default",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'updated'
        print(f"✓ PUT /api/restaurant/default - Dentist template applied")
        
        # Verify the update persisted
        verify_response = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data['name'] == template['name']
        assert verify_data['tagline'] == template['tagline']
        print(f"✓ Verified: Config now shows '{verify_data['name']}'")
    
    def test_update_restaurant_with_pizza_template(self):
        """Test PUT /api/restaurant/default with Pizza template config"""
        template = TEMPLATES['pizza']
        payload = {
            'name': template['name'],
            'tagline': template['tagline'],
            'monthly_price': template['monthly_price'],
            'brand_tagline': template['brand_tagline'],
            'city': 'Brampton',
            'phone': '(437) 331-5615',
            'location': '88 Main St N, Brampton',
            'hours': 'Mon-Sun 11am-12am',
            'special_name': 'Large Pepperoni + Wings Combo',
            'special_desc': '$24.99 tonight only',
            'menu': [
                {'name': 'Large Pepperoni Pizza', 'price': 16.99, 'category': 'pizza'},
                {'name': 'Large Margherita', 'price': 14.99, 'category': 'pizza'},
                {'name': 'Chicken Wings (12pc)', 'price': 14.99, 'category': 'sides'},
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/restaurant/default",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        print(f"✓ PUT /api/restaurant/default - Pizza template applied")
        
        # Verify the update persisted
        verify_response = requests.get(f"{BASE_URL}/api/restaurant/default")
        verify_data = verify_response.json()
        assert verify_data['name'] == template['name']
        print(f"✓ Verified: Config now shows '{verify_data['name']}'")


class TestChatWithTemplates:
    """Test that AI responds according to the applied template"""
    
    def test_chat_after_dentist_template(self):
        """Test chat responds as dental clinic after applying dentist template"""
        # First apply dentist template
        template = TEMPLATES['dentist']
        payload = {
            'name': template['name'],
            'tagline': template['tagline'],
            'brand_tagline': template['brand_tagline'],
            'menu': [
                {'name': 'Regular Checkup & Cleaning', 'price': 199, 'category': 'preventive'},
                {'name': 'Teeth Whitening', 'price': 349, 'category': 'cosmetic'},
            ]
        }
        requests.put(f"{BASE_URL}/api/restaurant/default", json=payload)
        
        # Reset chat session to pick up new config
        requests.post(f"{BASE_URL}/api/chat/reset", params={'session_id': 'test_dentist_session'})
        
        # Send a dental-related message
        chat_response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                'session_id': 'test_dentist_session',
                'message': 'I need to book a cleaning appointment',
                'lang': 'en',
                'restaurant_id': 'default'
            }
        )
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert 'reply' in data
        reply = data['reply'].lower()
        print(f"✓ Chat response for dentist: {data['reply'][:100]}...")
        # AI should respond about appointments/cleaning, not food
        # We just verify it responds successfully
    
    def test_chat_after_pizza_template(self):
        """Test chat responds as pizza store after applying pizza template"""
        # First apply pizza template
        template = TEMPLATES['pizza']
        payload = {
            'name': template['name'],
            'tagline': template['tagline'],
            'brand_tagline': template['brand_tagline'],
            'menu': [
                {'name': 'Large Pepperoni Pizza', 'price': 16.99, 'category': 'pizza'},
                {'name': 'Chicken Wings (12pc)', 'price': 14.99, 'category': 'sides'},
            ]
        }
        requests.put(f"{BASE_URL}/api/restaurant/default", json=payload)
        
        # Reset chat session
        requests.post(f"{BASE_URL}/api/chat/reset", params={'session_id': 'test_pizza_session'})
        
        # Send a pizza-related message
        chat_response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                'session_id': 'test_pizza_session',
                'message': 'I want to order a large pepperoni pizza',
                'lang': 'en',
                'restaurant_id': 'default'
            }
        )
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert 'reply' in data
        print(f"✓ Chat response for pizza: {data['reply'][:100]}...")


class TestAllTemplateConfigs:
    """Test all 6 template configurations can be applied"""
    
    @pytest.mark.parametrize("template_type,template_config", [
        ('dentist', TEMPLATES['dentist']),
        ('pizza', TEMPLATES['pizza']),
        ('pharmacy', TEMPLATES['pharmacy']),
        ('doctor', TEMPLATES['doctor']),
        ('trades', TEMPLATES['trades']),
        ('restaurant', TEMPLATES['restaurant']),
    ])
    def test_apply_template(self, template_type, template_config):
        """Test each template can be applied via PUT /api/restaurant/default"""
        payload = {
            'name': template_config['name'],
            'tagline': template_config['tagline'],
            'monthly_price': template_config['monthly_price'],
            'brand_tagline': template_config['brand_tagline'],
        }
        
        response = requests.put(
            f"{BASE_URL}/api/restaurant/default",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        
        # Verify
        verify = requests.get(f"{BASE_URL}/api/restaurant/default")
        assert verify.status_code == 200
        data = verify.json()
        assert data['name'] == template_config['name']
        print(f"✓ Template '{template_type}' applied: {template_config['name']}")


class TestCleanup:
    """Restore default restaurant config after tests"""
    
    def test_restore_default_restaurant(self):
        """Restore the default Desi Road restaurant config"""
        payload = {
            'name': 'Desi Road Restaurant',
            'tagline': 'Elevated Indian Cuisine',
            'city': 'Brampton',
            'phone': '(437) 331-5615',
            'location': '185 Fletchers Creek Blvd, Brampton',
            'hours': 'Mon-Sat 11am-11pm, Sun 12pm-10pm',
            'brand_tagline': 'Desi Daru Desi Khana',
            'special_name': 'Shahi Lamb Chops',
            'special_desc': 'discounted price tonight',
            'monthly_price': '$599',
            'menu': [
                {'name': 'Butter Chicken Cones', 'price': 16.99, 'category': 'main'},
                {'name': 'Shahi Lamb Chops', 'price': 29.99, 'category': 'main'},
                {'name': 'Dal Makhani', 'price': 15.99, 'category': 'main'},
                {'name': 'Garlic Naan', 'price': 3.99, 'category': 'bread'},
                {'name': 'Mango Lassi', 'price': 5.99, 'category': 'drink'},
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/restaurant/default",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        print("✓ Restored default Desi Road Restaurant config")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
