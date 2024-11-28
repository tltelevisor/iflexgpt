let gl_topic = 0
let last_prd
prbl0 = document.getElementById("0-prdblock");
let allPrdBlock = document.querySelectorAll('[id^="prdblock-"]');
const messagesContainer = document.getElementById('messages');
const slct_prdctsContainer = document.getElementById('prdcts-file-container');

//toggleLoader()

//Ожидание загрузки
function toggleLoader() {
  const loader = document.getElementById('loader')
  loader.classList.toggle('answ-hidden')
}

//Открытие-закрытие левого меню тем
function openSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open_fl');
}
function toggleMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

//Открытие-закрытие правого меню сайта
const navbarToggler = document.getElementById('navbar-toggler');
const navbarMenu = document.getElementById('custom-navbar-menu');
function openMenu() {
    const isExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
//    console.log(isExpanded)
    navbarToggler.setAttribute('aria-expanded', !isExpanded);
    navbarMenu.classList.toggle('active');
}

//Выбор прошлой темы

function getPosts(topic) {
const url_t = './topic'
    gl_topic = topic
    fetch(url_t, {
        method: 'POST',
        body: JSON.stringify(topic),
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
    .then((response) => response.json())
    .then((data) => {

    slct_prdctsContainer.classList.add('hidden');
    //slctd_prdctsContainer.classList.add('visible');
    messagesContainer.classList.add('visible');

    var map = new Map(Object.entries(data));
    topicMessage(map.get('topic_posts'));
    topicContext(map.get('context'));
    //old_message = data['previous_posts']
    }
    )
}

//Отображение сообщений из выбранной темы
function topicMessage(data) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
        data.forEach((ed) => {
          var map = new Map(Object.entries(ed));
          for (let [key, value] of map) {
                addMessage(`${value}`,`${key}`)}
        })
}

async function sendMessage_1() {
toggleLoader()
await timeout(3000);
addMessage('Привет! Как я могу помочь?', 'assistant');
toggleLoader()
}

//setTimeout(() => {
//    addMessage('Привет! Как я могу помочь?', 'assistant');
//}, 1000);
function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
async function sleep(fn, ...args) {
    await timeout(3000);
    return fn(...args);
}



//Отправка запроса к чату
async function sendMessage() {
toggleLoader()
    const url_s = '/send'
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (message === "") return;

    addMessage(message, 'user');
    userInput.value = '';

    // Симуляция ответа "ассистента"
//    setTimeout(() => {
//        addMessage('Привет! Как я могу помочь?', 'assistant');
//    }, 1000);
context = getContext()
send_json = JSON.stringify({'topic' : gl_topic, 'context' : context, "message" : message})

    await fetch(url_s, {
        method: 'POST',
        body: send_json,
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
    .then((response) => response.json())
    .then((data) => {
    //console.log(data);
    addMessage(data[0], 'assistant');
    if (data[1] != gl_topic){addTopic(data[1], message.substr(0, 64))}
    if (data[2]) AddFaqAnswer(data[2]);
    }
    )
//    .then(toggleLoader());
      toggleLoader();
}
//Добавляет в описание продукта ответы из FAQ ????
function AddFaqAnswer(prds) {
prds.forEach((ep) => {
prbl = document.getElementById("prdblock-" + ep[0]);
//Добавить к краткому описанию ответ из FAQ
//const answ = document.createElement('span');
//answ.textContent = ep[1] + ":" + " " + ep[2];
//prbl.appendChild(answ)
prbl.innerText = ep[1] + ":" + " " + ep[2];
//Заместить краткое описание ответом из FAQ


//console.log(ep[0],ep[1],ep[2])
})
}


//Добавления сообщений в чатбокс
function addMessage(text, sender) {
    messagesContainer.classList.add('visible');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const bubbleDiv = document.createElement('div');
    bubbleDiv.classList.add('bubble');
    bubbleDiv.textContent = text;

    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
//Добавление темы в левую панель
function addTopic(t_id, t_text) {
//let id_t = 35;
//let text_t = 'новая тема';
const topicContainer = document.getElementById('topics');

    const topicDiv = document.createElement('li');
    const topic_a = document.createElement('a');
    //<a class="nav-link" href="javascript:void(0);" onclick="getPosts('5')">
    topic_a.textContent = t_text;
    topic_a.setAttribute("class", "nav-link");
    topic_a.href = "javascript:void(0);"
    topic_a.setAttribute("onclick","getPosts('" + t_id + "')");
//    console.log(topic_a)
//    topicDiv.appendChild(topic_a);
//    console.log(topicDiv)
//    topicContainer.prepend(topicDiv);
    topicContainer.prepend(topic_a);
}


//очистить чат из предыдущих сообщений
function clearChat() {
    messagesContainer.innerHTML = ''; // Очищаем содержимое блока сообщений
    gl_topic = 0 // 0 - признак новой темы
    // Скрываем окно чата, если сообщений нет
    slct_prdctsContainer.classList.remove('hidden');
    //slctd_prdctsContainer.classList.remove('visible');
    messagesContainer.classList.remove('visible');
}

//по кнопке изменить контекст скрыть-отобразить блоки. Для удаления.
function change_context() {
    const ch_cntxt = document.getElementById('ch_cntxt');
    //slctd_prdctsContainer.classList.remove('visible');
    slct_prdctsContainer.classList.remove('hidden');
}

//Динамическое изменение блоков выбора контекста и вывод краткой информации о выбранном продукте
function chk_prd(prd_id) {
    //document.getElementById('clfile-0').style.display = "none";
    let allFileDiv = document.querySelectorAll('[id^="clfile-"]');
    let allPrdChk = document.querySelectorAll('input[type="checkbox"][id^="chkprd-"]:checked');


    prch = document.getElementById("chkprd-" + prd_id);
    fdiv = document.getElementById("clfile-" + prd_id);
    prbl = document.getElementById("prdblock-" + prd_id);


    allFileDiv.forEach((efd) => {
    efd.style.display = "none";
    });
    allPrdBlock.forEach((efd) => {
    efd.style.display = "none";
    });
//    document.getElementById('0-clfile').style.display = "none";

    if (prch.checked) {fdiv.style.display = "flex";

    getPrdShr(prd_id)
        .then(data => prbl.innerText = data)
        .catch(error => console.error('Ошибка:', error));
//    console.log('textt', textt.then());
    prbl0.style.display = "none";
    prbl.style.display = "flex";}
    else {fdiv.style.display = "none";
        prbl.style.display = "none";
        fdiv.querySelectorAll('input[type="checkbox"]').forEach((efchk) => {
        efchk.checked = false;})

        if (allPrdChk[0]) {
            let pr_id = allPrdChk[0].id.substring(7);
            getPrdShr(pr_id)
//                .then(data => console.log("prdblock-" + pr_id, data))
                .then(data => document.getElementById("prdblock-" + pr_id).innerText = data)
                .catch(error => console.error('Ошибка:', error));
            document.getElementById("prdblock-" + pr_id).style.display = "flex";
//            document.getElementById("prdblock-" + allPrdChk[0].id.substring(7)).style.display = "flex";
            document.getElementById("clfile-" + allPrdChk[0].id.substring(7)).style.display = "flex";
            }
        else
            prbl0.style.display = "flex";
//            document.getElementById('0-clfile').style.display = "flex";
      }
    }
//Запрос краткого описания продукта из формы index.html
//async function getData(url) {
//  const response = await fetch(url);
//  return await response.json();
//}
//async function getPrdShr(pr_id) {
//const url_t = '/getprshr'
//    const result = await fetch(url_t, {
//        method: 'POST',
//        body: JSON.stringify(pr_id),
//        headers: {
//        'Content-type': 'application/json; charset=UTF-8',
//        },
//    })
//    return await result.json().data;
//}

async function getPrdShr(pr_id) {
    const url_t = '/getprshr'
    try {
        let response = await fetch(url_t, {
        method: 'POST',
        body: JSON.stringify(pr_id),
        headers: {
        'Content-type': 'application/json; charset=UTF-8',
        },
    })
        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }
        let data = await response.json();
        return data;
    } catch (error) {
        console.error('Ошибка запроса:', error);
        return null;
    }
}

//Получение выбранного контекста в переменную
function getContext() {
const context = [...document.querySelectorAll('[id^="chkprd-"], [id^="chkfile-"], [id^="chkcat-"]')]
                            .filter(checkbox => checkbox.checked)
                            .map(checkbox => checkbox.id);
    return context
    }

//Отображение полученного контекста из выбранной темы (topic).
function topicContext(data) {

document.getElementById('prdcts-file-container').querySelectorAll('input[type="checkbox"]').forEach((efchk) => {
        efchk.checked = false;})
document.getElementById('context').querySelectorAll('input[type="checkbox"]').forEach((efchk) => {
        efchk.checked = false;})
let allFileDiv = document.querySelectorAll('[id^="clfile-"]');
    allFileDiv.forEach((efd) => {
    efd.style.display = "none";
    });

if (data) {

var map = new Map(Object.entries(data));

if (map.get('cat')) {
map.get('cat').forEach((ep)=> {
          document.getElementById("chkcat-" + ep).checked = true;
        })}
if (map.get('prd')) {
map.get('prd').forEach((ep)=> {
          document.getElementById("chkprd-" + ep).checked = true;
          const prbl = document.getElementById("prdblock-" + ep);
           prbl0.style.display = "none";
           allPrdBlock.forEach((efd) => {
            efd.style.display = "none";
            });
           prbl.style.display = "flex";
          getPrdShr(ep)
            .then(data => prbl.innerText = data)
            .catch(error => console.error('Ошибка:', error));
        })}
if (map.get('file')) {
map.get('file').forEach((ep)=> {
          document.getElementById("chkfile-" + ep).checked = true;
        })}
let allFileChk = document.querySelectorAll('input[type="checkbox"][id^="chkfile-"]:checked');

if (allFileChk[0]) {

allFileChk[0].parentElement.parentElement.style.display = "flex"}

}
}


