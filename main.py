import pypdf
import re
import logging
from pathlib import Path

logging.getLogger().setLevel(logging.INFO)

def main():
    ## Get all files
    folder_path = Path('input')
    registers = []
    for doc in folder_path.iterdir():
        if doc.is_file() and doc.name != '.gitkeep':
           registers.extend(processDoc(doc))
    save(registers)

def find_monetary(text):
    return re.search("[0-9]+,[0-9]{2}", text)

def find_total(text):
    return re.search("Total dos lançamentos atuais", text)

def find_iof(text):
    return re.search("Repasse de IOF em R\$", text)

def find_date(text):
    match = re.search("^([0-9]{2})/([0-9]{2})$", text)
    if not match:
        return None
    day = int(match.group(1))
    month = int(match.group(2))
    return [day, month]

def find_postage_date(text):
    match = re.search(r"Postagem:\s\d{2}/(\d{2})/(\d{4})", text)
    if match:
        month = int(match.group(1))
        year = int(match.group(2))
        return [month, year]

def get_visitor_body(array, page):
    def visitor_body_fn(text, cm, tm, font_dict, font_size):
        if text == "":
            return
        x = tm[4]
        y = tm[5]    
        section = 0
        if (145 < x < 355):
            section = 1
        if (360 < x < 800):
            section = 2

        if section == 0:
            return
        
        array.append({
            "page": page,
            "x": x,
            "y": y,
            "text": text,
            "section": section
        })
         
    return visitor_body_fn

def groupPageText(array, pages):
    textArray = []

    for page in pages:
        pageArray =  list(filter(lambda x: x['page'] == page, array))
        minYPage = 0
        for item in pageArray:
            if item['text'].lower() == 'continua...':
                minYPage = item['y']

            if find_total(item['text']):
                nextItem = pageArray[pageArray.index(item)+1]
                textArray.append(item['text'])
                textArray.append(nextItem['text'])
            
        for section in [1, 2]:
            minYSection = 0
            maxYSection = 0
            sectionArray = list(filter(lambda x: x['section'] == section, pageArray))
            for item in sectionArray:
                if item['text'].lower() == 'compras parceladas - próximas faturas':
                    minYSection = item['y']
                if item['text'].lower() in ["lançamentos: compras e saques", "lançamentos: produtos e serviços", "lançamentos internacionais", "total dos lançamentos atuais"]:
                    maxYSection = max(maxYSection, item['y'])
            
            sectionArrayB = list(filter(lambda x: 
                                        x['y'] > max(minYPage, minYSection) and 
                                        x['y'] < maxYSection ,sectionArray) )        
            textArray.extend(list(map(lambda x: x['text'], sectionArrayB)))
    ## print (textArray)
    return textArray

def processDoc(doc):
    doc_name = doc.name
    reader = pypdf.PdfReader(doc)
    pages = [i for i in range(1, len(reader.pages)-2)]
    dict = {
        "doc_name": doc_name,
        "month": None,
        "year": None
    }

    ## Get month and year
    first_page = reader.pages[0].extract_text().split('\n')
    for line in first_page:
           postage_date = find_postage_date(line)
           if postage_date:
                dict['month'], dict['year'] = postage_date
                continue
           

    ## Get all data from pages with tables
    parts = []
    for page in pages:
        pageParts = []
        reader.pages[page].extract_text(visitor_text=get_visitor_body(pageParts, page))
        
        parts.extend(pageParts)
    
    logging.debug(f'"{doc.name}" pages: ' + str(len(reader.pages)))
    return processParts(dict, groupPageText(parts, pages))

def processParts(dict, parts):
    doc_name = dict['doc_name']
    month = dict['month']
    year = dict['year']
    sum = 0
    total_value = 0
    register = None
    registers = []
    for index in range(len(parts)):
        currentLine = parts[index]
        logging.debug(f'line: {currentLine}')

        if find_total(currentLine):
            total_value = float(parts[index+1].replace('.', '').replace(',', '.').replace(' ', ''))
            continue

        date = find_date(currentLine)
        if date:
            logging.debug('starting register')
            dateYear = year - 1 if date[1] == 12 and month == 1 else year
            register = [doc_name, f"{date[0]}/{date[1]}/{dateYear}"]
            continue

        if register and find_monetary(currentLine):
            logging.debug('closing register')
            value = float(currentLine.replace('.', '').replace(',', '.').replace(' ', ''))
            sum+=value
            category = parts[index+1] if index + 1 < len(parts) else ''

            category_name = category.split('.')[0].strip()
            city = '.'.join(category.split('.')[1:]).strip()

            register += [category_name, city]
            register.append(value)            
            registers.append(register)            
            register = None
            continue

        if (find_iof(currentLine)):
            value = float(parts[index+1].replace('.', '').replace(',', '.').replace(' ', ''))
            sum+=value        
            registers.append([doc_name, f"15/{month}/{year}", "IOF", "", "", "", "", value])            
            continue

        if register:
            logging.debug('complementing register')
            _register = currentLine
            _parc = re.search("[0-9]{2}/[0-9]{2}", _register)
            _parc, _total = _parc.group().split('/') if _parc else ["", ""]
            register += [_register, _parc, _total]     
            continue
    if round(sum, 2) != total_value:
        logging.error(f"Values don't match. Sum: {sum}, Total: {total_value}, doc_name: {doc_name}")
        # logging.error(registers)
        logging.error(list(map(lambda x: f"{x[2]}{x[-2]}{x[-1]}", registers)))
        
        raise Exception("Values don't match")
    
    logging.debug(f'"{doc_name}" total value: ' + str(round(sum, 2)))
    logging.debug(f'"{doc_name}" registers  : ' + str(len(registers)))
    return registers

def save(registers):
    sep = ';'
    with open('output/ouput.csv', 'w') as f:
        t = [[register if isinstance(register, str) else str(register).replace('.',',') for register in row] for row in registers]
        data = sep.join(['filename','date','description','parc','total_parc','category','city','value']) + '\n'
        data += '\n'.join([ sep.join(register) for register in t])
        f.write(data)
        
    logging.debug(registers)
    logging.info('total of registers ' + str(len(registers)))
    logging.info('total of money ' + str(sum([r[-1] for r in registers])))

if __name__ == "__main__":
    main()