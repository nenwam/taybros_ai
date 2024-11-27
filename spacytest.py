import re
import json
import pdfplumber

def extract_text_from_pdf(file_path):
    # Open the PDF file
    with pdfplumber.open(file_path) as pdf:
        text = ''
        # Iterate through each page
        for page in pdf.pages:
            # Extract text from the page
            text += page.extract_text() + '\n'
    return text

def extract_subitems(text):
    subitems = []
    
    # Regular expression to match lines ending with a price
    # Assumes prices are in the format of a number with optional commas and decimals
    pattern = re.compile(r'(.+?)\s+([\d,]+\.\d{2})$')
    
    for line in text.split('\n'):
        line = line.strip()
        match = pattern.search(line)
        if match:
            product_name = match.group(1).strip()
            price = match.group(2).strip()
            subitems.append({'product_name': product_name, 'price': price})
    
    return subitems

# def extract_subitems_with_descriptions(text):
#     subitems = []
    
#     # Regular expression to match lines ending with a price
#     pattern = re.compile(r'(.+?)\s+([\d,]+\.\d{2})$')
    
#     lines = text.split('\n')
#     i = 0
#     while i < len(lines):
#         line = lines[i].strip()
#         match = pattern.search(line)
        
#         if match:
#             product_name = match.group(1).strip()
#             price = match.group(2).strip()
#             description = []
            
#             # Check for description lines following the subitem
#             i += 1
#             while i < len(lines) and not pattern.search(lines[i].strip()):
#                 description.append(lines[i].strip())
#                 i += 1
            
#             subitems.append({
#                 'product_name': product_name,
#                 'price': price,
#                 'description': ' '.join(description) if description else None
#             })
#         else:
#             i += 1
    
#     return subitems

def marvin_extract(text):
    subitems = []
    
    # Regular expression to match lines ending with a price
    pattern = re.compile(r'(.+?)\s+([\d,]+\.\d{2})$')
    
    # Performance metrics and tax-related terms to skip
    skip_terms = ['u-factor', 'solar heat gain coefficient', 'visible light transmittance',
                 'condensation resistance', 'cpd number', 'performance information']
    
    # Tax terms to always skip regardless of price
    tax_terms = ['tax', 'taxable']
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = pattern.search(line)
        
        if match:
            product_name = match.group(1).strip()
            price = match.group(2).strip()
            price_value = float(price.replace(',', ''))
            
            # Skip lines with total, subtotal, net total
            if any(x in product_name.lower() for x in ['total', 'subtotal', 'net']):
                i += 1
                continue
                
            # Skip if line contains tax terms regardless of price
            if any(term in line.lower() for term in tax_terms):
                i += 1
                continue
                
            # Skip if line contains other skip terms AND price is < 1.01
            skip_current = any(term in line.lower() for term in skip_terms) and price_value < 1.01
            if not skip_current:
                description = []
                
                # Check for description lines following the subitem
                i += 1
                while i < len(lines):
                    desc_line = lines[i].strip()
                    next_match = pattern.search(desc_line)
                    
                    # Break if we find another price line
                    if next_match:
                        break
                        
                    # Only add description line if it doesn't contain skip terms
                    if not any(term in desc_line.lower() for term in skip_terms):
                        description.append(desc_line)
                    i += 1
                
                subitems.append({
                    'product_name': product_name,
                    'price': price,
                    'description': ' '.join(description) if description else None
                })
                continue
            
            i += 1
        else:
            i += 1
    
    return subitems

def tmcobb_extract(text):
    subitems = []
    
    # Regular expression to match lines with a quantity and two prices
    pattern = re.compile(r'(.+?)\s+(\d+)\s+([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})$')
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = pattern.search(line)
        
        if match:
            product_name = match.group(1).strip()
            quantity = int(match.group(2).strip())
            # First price is the unit price, second is the extended price
            unit_price = match.group(3).strip()
            price = match.group(4).strip()
            
            description = []
            
            # Check for description lines following the subitem
            i += 1
            while i < len(lines):
                desc_line = lines[i].strip()
                # Break if a new subitem is found
                if pattern.search(desc_line):
                    break
                description.append(desc_line)
                i += 1
            
            subitems.append({
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'price': price,
                'description': ' '.join(description) if description else None
            })
        else:
            i += 1
    
    return subitems

def fleetwood_extract(text):
    subitems = []
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for the product name line and validate item number format
        if line.startswith("ITEM:"):
            # Extract and validate item number
            product_name = line.split("ITEM:")[1].strip()
            item_number_match = re.match(r'(\d+)-0\s+', product_name)
            
            if item_number_match:  # Only process items with format "X-0"
                # Remove the item number from product name
                product_name = product_name[product_name.find(' '):].strip()
                
                # Remove "QTY Each Resale Price" and "QTY Each Dealer-Cost" from product name
                if "QTY Each Resale Price" in product_name:
                    product_name = product_name.replace("QTY Each Resale Price", "").strip()
                if "QTY Each Dealer-Cost" in product_name:
                    product_name = product_name.replace("QTY Each Dealer-Cost", "").strip()
                
                # Move to the next line to find quantity and price
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Look for the line with quantity and price
                    match = re.search(r'(\d+)\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})', next_line)
                    if match:
                        quantity = int(match.group(1))
                        unit_price = match.group(2)
                        price = match.group(3)
                        
                        # Collect only specific description lines until the next "ITEM:"
                        description = []
                        i += 1
                        while i < len(lines) and not lines[i].strip().startswith("ITEM:"):
                            desc_line = lines[i].strip()
                            # Only include lines starting with Finish, Hardware, Frame, or Glazing
                            if any(desc_line.startswith(prefix) for prefix in ["Finish:", "Hardware:", "Frame:", "Glazing:"]):
                                # Remove "________ init." from description line
                                desc_line = desc_line.replace("________ init.", "").strip()
                                desc_line = desc_line.replace("________ init", "").strip()
                                description.append(desc_line)
                            i += 1
                        
                        subitems.append({
                            'product_name': product_name,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'price': price,
                            'description': ' '.join(description) if description else None
                        })
                        break
                    else:
                        i += 1
            else:  # Skip items that don't match the X-0 format
                i += 1
        else:
            i += 1
    
    return subitems

def trustile_extract(text):
    subitems = []
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for the header line
        if line == "Line Label Qty UOM Description Unit Extended":
            i += 1 # Move to product line
            while i < len(lines):
                product_line = lines[i].strip()
                
                # Skip empty lines or page headers
                if not product_line or "TruStile Doors, LLC" in product_line:
                    i += 1
                    continue
                    
                # Check if we've reached the end of products
                if product_line.startswith("Total Units:"):
                    break
                    
                # Extract product info
                parts = product_line.split('EACH')
                if len(parts) == 2:
                    # Get label/product name from first part
                    product_name = parts[0].strip()
                    
                    # Get description and prices from second part
                    desc_prices = parts[1].strip()
                    
                    # Extract quantity - look for number before EACH/EA
                    qty_match = re.search(r'(\d+)\s*(?:EACH|EA)$', product_name)
                    quantity = int(qty_match.group(1)) if qty_match else 1
                    
                    # Remove quantity and EACH/EA from product name
                    product_name = re.sub(r'\s*\d+\s*(?:EACH|EA)$', '', product_name)
                    
                    # Extract unit and extended prices
                    price_match = re.search(r'\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})', desc_prices)
                    if price_match:
                        unit_price = price_match.group(1)
                        price = price_match.group(2)
                        
                        # Get description by collecting lines until next product
                        # Remove price info from description
                        desc_text = desc_prices[:desc_prices.find('$')].strip()
                        description = [desc_text]
                        
                        next_i = i + 1
                        while next_i < len(lines):
                            next_line = lines[next_i].strip()
                            if not next_line or "TruStile Doors, LLC" in next_line:
                                next_i += 1
                                continue
                            if "Line Label Qty UOM Description Unit Extended" in next_line or \
                               next_line.split('EACH')[0].strip().split('-')[0].strip().replace('No #','').strip().isdigit() or \
                               next_line.startswith("Total Units:"):
                                break
                            description.append(next_line)
                            next_i += 1
                            
                        subitems.append({
                            'product_name': product_name,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'price': price,
                            'description': ' '.join(description)
                        })
                
                i += 1
        i += 1
            
    return subitems

def convert_to_json(subitems, output_file='output.json'):
    # Prepare the data in the required format
    rows = [
        {
            "ref": "",
            "bill": "",
            "date": "",
            "quantity": str(subitem.get('quantity', '')),
            "description": subitem.get('description', ''),
            "cost": subitem.get('unit_price', ''),
            "sell": subitem.get('price', '')
        }
        for subitem in subitems
    ]
    
    # Write the data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=4)

    return rows


file_path = 'TruStile1.pdf'
extracted_text = extract_text_from_pdf(file_path)
subitems = trustile_extract(extracted_text)
convert_to_json(subitems)

with open('spacyoutput.txt', 'w', encoding='utf-8') as f:
    for subitem in subitems:
        f.write(f"Product: {subitem['product_name']}, Quantity: {subitem['quantity']}, Price: {subitem['price']}\n, Description: {subitem['description']}\n")
    f.write(f"\nTotal number of subitems: {len(subitems)}")

# Write results to spacyoutput.txt
# with open('spacyoutput.txt', 'w', encoding='utf-8') as f:
#     for subitem in subitems:
#         f.write(f"Product: {subitem['product_name']}, Price: {subitem['price']}\n")
#     f.write(f"\nTotal number of subitems: {len(subitems)}")
