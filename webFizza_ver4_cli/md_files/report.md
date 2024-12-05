| Severity | Payload | Vulnerability | Form Method | Page Url | Status Code |
| --- | --- | --- | --- | --- | --- |
| Low | ><img src=x onerror=alert('Reflected XSS')> | Reflected XSS | post | http://testphp.vulnweb.com/ | 200 |
| High | <script>alert('Reflected XSS')</script> | Reflected XSS | post | http://testphp.vulnweb.com/ | 200 |

