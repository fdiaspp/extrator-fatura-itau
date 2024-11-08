import PyPDF2
import re
import logging
import sys


logging.getLogger().setLevel(logging.DEBUG)


tokens = None
registers = []
index = 0
doc_name = None

def next():
    global index
    index += 1
    return current()


def next_document():
    global doc_name

    docs = sys.argv[1:]
    for doc in docs:
        doc_name = doc.split('/')[-1]
        reader = PyPDF2.PdfReader(doc)
        logging.info(f'Number of pages in "{doc}": ' + str(len(reader.pages)))
        yield reader


def next_page():
    global index
    global tokens

    for reader in next_document():
        for page in reader.pages:
            tokens = page.extract_text().split('\n')
            index = 0
            yield True

def current(offset=0):
    return tokens[index+offset] if index+offset < len(tokens) else None


def find_monetary(text):
    return re.search("[0-9]+,[0-9]{2}", text)


def find_date(text):
    return re.search("^[0-9]{2}/[0-9]{2}$", text)    

register = None
is_correct_table = False

for page in next_page():
    while next():
        logging.debug(current())

        if current().lower() in ["lançamentos: compras e saques", "lançamentos: produtos e serviços"]:
            is_correct_table = True
            continue

        if current().lower() in ["compras parceladas - próximas faturas"]:
            is_correct_table = False
            continue

        if find_date(current()) and is_correct_table:
            logging.debug('starting register')
            register = [doc_name, current()]
            continue

        if find_monetary(current()) and register:
            logging.debug('closing register')
            value = float(current().replace(',', '.').replace(' ', ''))
            
            category = ""
            for i in range(1,7):
                offset = current(offset=i)
                logging.debug(f'category attemp {i}: {offset}')
                if offset and '.' in offset and ',' not in offset:
                    category = offset
                    break
            
            category_name = category.split('.')[0].strip()
            city = '.'.join(category.split('.')[1:]).strip()

            register += [category_name, city]
            register.append(value)            
            registers.append(register)            
            register = None
            continue

        if register:
            logging.debug('complementing register')
            _register = current()
            _parc = re.search("[0-9]{2}/[0-9]{2}", _register)
            _parc, _total = _parc.group().split('/') if _parc else ["", ""]
            register += [_register, _parc, _total]     
            continue
  
sep = ';'
with open('ouput.csv', 'w') as f:
    t = [[register if isinstance(register, str) else str(register).replace('.',',') for register in row] for row in registers]
    data = sep.join(['filename','date','description','parc','total_parc','category','city','value']) + '\n'
    data += '\n'.join([ sep.join(register) for register in t])
    f.write(data)

logging.debug(registers)
logging.info('total of registers ' + str(len(registers)))
logging.info('total of money ' + str(sum([r[-1] for r in registers])))
