import os
import re

NEW_COOKIE = '.eJyllsFuFDEMht8l51LtQCVgTvAMSFyqauR1vFurSRxszyK16rujWXZKBQVtzZwcJd8f-5cdzUPqpJVNLI0PacsOKApLDOgzFL4HTePmIqHSKaLCldtpUYg0jcPjxRM7HeiWcS7yu8jwJDI8FxmeiyA47UUZLEQXpuYUY6WysbQgrZTZJcRmsNutgOaI61S7ksXsIkNoy-L16I6La6zc_cyh_qqgGKuzEkJjjKVbySWLTR32oY6ukucSu7qJ844RMNyWopnahFL7nzN9Nh-7evErBpLuuEQ6pKvkGYNT2FWqxJ3uKgeiLBrDv4WmUKmLvvDenWPWyk5kDpnNXxqQ84SsQ8n_goe_w1JihhnpgZFlWof7f0RiGbjgXQiccVaDYOEOBjbBAdo95Nh76Ix35CF0thk0aNj6X2Cvh391ynX6nCs3NlfIoulmyYl0gk6lcJY0pi9sThXSaQcpzwXSmL6-2Zy-dYsqLC9NgkXykys0g4JwiVLXIzvxRfMYD9Pw_sPm6t3H4e3V5Xfa9vUQ52O2x7hJ3Sql8Wee6wnnvshQ7YUgS3r8AYDQGKo.ak7mig.Ph0qT2GCwIr4osfWId-YwSVIZzg'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
updated = []
skipped = []

for root, dirs, files in os.walk(BASE_DIR):
    for fname in files:
        if fname.endswith('.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'Cookie: session=' in content:
                new_content = re.sub(r'Cookie: session=[^\r\n]+', f'Cookie: session={NEW_COOKIE}', content)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                rel = os.path.relpath(fpath, BASE_DIR)
                updated.append(rel)
            else:
                skipped.append(fname)

print(f"\n[OK] Archivos actualizados ({len(updated)}):")
for f in updated:
    print(f"   + {f}")

if skipped:
    print(f"\n[--] Sin cookie (omitidos):")
    for f in skipped:
        print(f"   - {f}")
