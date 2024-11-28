const prd_id = document.getElementById('prdctid').getAttribute('name')

let faq_id
  const e_q = document.getElementById('question');
  const e_a = document.getElementById('answer');
  const cntCat = document.getElementById('cat');


//перенос текста из описания категорий для редактирования
function editFaq(id) {
 const faq_a = document.getElementById('ans-' + id);
 const cat = document.getElementById('cat-' + faq_a.getAttribute('for'));
 document.getElementById('cat_faq').innerText = cat.innerText;
 document.getElementById('cat_faq').setAttribute('for', id);
//    e_q.style.height = `25px`;
//  e_a.style.height = `25px`;
  e_q.style.height = '25px';
  e_a.style.height = '25px';
//or innerText
//  e_q.innerText = document.getElementById('qst-' + id).innerText;
//  e_a.innerText = document.getElementById('ans-' + id).innerText;
    e_q.value = document.getElementById('qst-' + id).innerText;
  e_a.value = document.getElementById('ans-' + id).innerText;
  e_q.style.height = `${e_q.scrollHeight}px`;
  e_a.style.height = `${e_a.scrollHeight}px`;
  e_a.focus()
  }

//Сохранение описаний категорий продукта в FAQ
  function saveFaq() {
    const url_t = '/svfaq'
    const quest = e_q.value;
    const answ = e_a.value;
    const faq_id = document.getElementById('cat_faq').getAttribute('for')
    fetch(url_t, {
        method: 'POST',
        body: JSON.stringify({'faq_id': faq_id, 'quest': quest, 'answ': answ}),
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
    .then(response => response.json())
        .then(data => {
        //document.getElementById('response').innerText = data['message'];
        if (data['error'] === '0') {
        console.log('----redirect', '/product/'+ prd_id);
        window.location.href ='/product/'+ prd_id}
        if (data['error'] === '1') {
        console.error('Error:', error)};
    })
    .catch(error => {
        console.log('---перед ошибкой');
//        document.getElementById('response').innerText = data['message'];
        console.error('Error:', error);
    });
}
//Запрос GPT заполнить описания продукта перед сохранением этого описания в категории
async function askGpt() {
toggleLoader()
    const url_s = '/askgpt';
    const quest = e_q.value;
    const message = e_q.value.trim();
    if (message === "") return;

context = getContext()
send_json = JSON.stringify({'context' : context, "message" : message})

    await fetch(url_s, {
        method: 'POST',
        body: send_json,
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
    .then((response) => response.json())
    .then((data) => {
    if (data) e_a.value = data;
    e_a.style.height = `${e_a.scrollHeight}px`;
    e_a.focus()
    }
    )
toggleLoader()
}



//console.log(prd_id)
//Выбор файла
function handleFiles(files) {
const btm = document.getElementById('btmfile')
    for (const file of files) {
    btm.innerText=file.name
//        console.log(file.name)
        };
    }

//Добавление файла
document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Пожалуйста, выберите файл!');
        return;
    }
    const formData = new FormData(uploadForm); //uploadForm
    formData.append('prd_id', prd_id);
//    console.log(formData)
//    for (var key of formData.keys()) {
//   console.log(key, formData.get(key))};

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())  // Обработка ответа сервера
    .then(data => {
        //document.getElementById('response').innerText = data['message'];
        if (data['error'] === '0') {
        console.log('----redirect', '/product_files/'+ prd_id);
        window.location.href ='/product_files/'+ prd_id }
        //console.log(data['file']);
    })
    .catch(error => {
        console.log('---перед ошибкой');
//        document.getElementById('response').innerText = data['message'];
        console.error('Error:', error);
    });
});

//Удаление файла

function delFile(file_id) {
const url_t = '/delete'
    fetch(url_t, {
        method: 'POST',
        body: JSON.stringify(file_id),
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
    .then(response => response.json())
        .then(data => {
        //document.getElementById('response').innerText = data['message'];
        if (data['error'] === '0') {
        console.log('----redirect', '/product_files/'+ prd_id);
        window.location.href ='/product_files/'+ prd_id}
        if (data['error'] === '1') {
        document.getElementById('response').innerText = data['message'];
        console.error('Error:', error)};
    })
    .catch(error => {
        console.log('---перед ошибкой');
//        document.getElementById('response').innerText = data['message'];
        console.error('Error:', error);
    });
}
