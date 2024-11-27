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

# Example usage
file_path = 'TruStile1.pdf'
extracted_text = extract_text_from_pdf(file_path)
# Write the extracted text to a txt file
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(extracted_text)