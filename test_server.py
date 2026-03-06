#!/usr/bin/env python
"""
Test if the Django server is working properly
"""
import urllib.request
import urllib.error

def test_url(url):
    """Test if a URL is accessible"""
    try:
        response = urllib.request.urlopen(url)
        print(f"✅ {url}")
        print(f"   Status: {response.status}")
        print(f"   Headers: {dict(response.headers)}")
        return True
    except urllib.error.HTTPError as e:
        print(f"⚠️  {url}")
        print(f"   HTTP Error: {e.code} - {e.reason}")
        if e.code == 302:
            print(f"   This is OK - server is redirecting to login")
            print(f"   Location: {e.headers.get('Location', 'unknown')}")
            return True
        return False
    except urllib.error.URLError as e:
        print(f"❌ {url}")
        print(f"   Error: {e.reason}")
        print(f"   Is the server running? Try: python manage.py runserver 6000")
        return False
    except Exception as e:
        print(f"❌ {url}")
        print(f"   Error: {e}")
        return False

print("="*60)
print("Testing Django Server")
print("="*60)
print()

# Test different URLs
urls = [
    "http://localhost:6000/",
    "http://127.0.0.1:6000/",
    "http://localhost:6000/login/",
    "http://localhost:6000/admin/",
]

for url in urls:
    test_url(url)
    print()

print("="*60)
print("Summary")
print("="*60)
print()
print("If you see 302 redirects or 200 OK, the server is working!")
print()
print("Access these URLs in your browser:")
print("  - http://localhost:6000/")
print("  - http://localhost:6000/login/")
print("  - http://localhost:6000/admin/")
print()
print("If you can't connect, make sure the server is running:")
print("  python manage.py runserver 6000")
print()
