let infoArr = []
let imgArr = []
let optArr = []
let keyData = /* 用于上传给“图生图”接口的对象数据 */
{
    "prompt": '', // 正向描述，用于获取bimarsh的训练结果
    "negative_prompt": "poor quality, blurry, distorted, out of frame, bad proportions", // 反向描述，用于隐藏掉你不希望出现的内容
    "batch_size": 3, // 出图数量
    // "n_iter": 3, // 出图数量（跟上面的"batch_size两选一）
    "steps": 30,
    "width": 512, // 出图宽度
    "height": 512, // 出图高度
    'resize_mode': 1,
    // 'inpaint_full_res_padding': 8,
    // 'mask_blur': 4,
    "cfg_scale": 7,
    "override_settings": {
        "sd_model_checkpoint": "xsarchitectural_v11.ckpt [631eea1a0e]",    
      },
    "init_images": [],//用于存储上传的背景图片
    "sampler_name": "DDIM",
    "save_images": false,
    "alwayson_scripts": {
        "controlnet": {
            "args": [
                {
                    "module": "inpaint_only+lama",
                    "model": "control_v11p_sd15_inpaint [ebff9138]",//局部重绘
                    'enabled': true,
                    'input_image': "",
                }
            ]
        }
    },
    "mask": "",//蒙版图，蒙版的作用在于专门在背景图片中划出一块区域来存储/显示训练结果
}
let keyDataClone = JSON.parse(JSON.stringify(keyData));
let keyDataArr = [];
keyDataArr.push({});         // keyDataArr[0]
keyDataArr.push(keyDataClone);//keyDataArr[1]

function inputVedio() {
    $('.mask').show()
    $('.mask').css({ "display": "flex", "justify-content": "center", "align-items": "center" })
}
function inputImg() {
    $('.mask1').show()
    $('.mask1').css({ "display": "flex", "justify-content": "center", "align-items": "center" })
}
function inputMask() {
    $('.mask2').show()
    $('.mask2').css({ "display": "flex", "justify-content": "center", "align-items": "center" })
}
function closePage() {
    $('.mask').hide()
}
function closePage1() {
    $('.mask1').hide()
}
function closePage2() {
    $('.mask2').hide()
}
function convertToBase64(url, callback) { //将图片转换为BASE64格式
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');
    var img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = function () {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        var base64Data = canvas.toDataURL('image/png');
        callback(base64Data);
    };
    img.src = url;
}
function uploadVedio(idx) { //上传视频
    const uploadVedio = document.getElementById('uploadVedio')
    uploadVedio.click();
    uploadVedio.addEventListener('change', function onFileInputChange(file) {
        file.preventDefault();
        const files = file.target.files[0];
        const fileURL = URL.createObjectURL(files);
        infoArr.push(fileURL);
        renderVideo(infoArr,idx);
        setTimeout(() => {
            let formData = new FormData()
            formData.append('file', files)
            if (!keyDataArr[idx].prompt)
                renderToImage(formData,idx)
        }, 1000);
        uploadVedio.value = '' //去清空本次对话内容
        uploadVedio.removeEventListener('change', onFileInputChange);
        // URL.revokeObjectURL(fileURL);// Free up memory by revoking the object URL
    })
}
function uploadImg(idx) { //背景环境手动上传图片
    let _saveImg = ``;
    const uploadBgi = document.getElementById('uploadBgi')
    uploadBgi.click()
    uploadBgi.addEventListener('change', function onFileInputChange(e) {
        e.preventDefault()
        const files = e.target.files[0]
        const fileURL = URL.createObjectURL(files);
        convertToBase64(fileURL, function (base64Img) {
            keyDataArr[idx].init_images.push(base64Img);
            keyDataArr[idx].alwayson_scripts.controlnet.args[0].input_image = base64Img;
            _saveImg += `
            <img src="${base64Img}" style="position:absolute;z-index:2;width:300px;height:300px;border-radius:15px;"></img>
            `;
            $('#img'+idx).append(_saveImg);
            $('.mask1').hide()
            uploadBgi.value = '' //去清空本次对话内容
            uploadBgi.removeEventListener('change', onFileInputChange);
            URL.revokeObjectURL(fileURL);
        });
    })
}
function uploadMaskImg(idx) { //背景环境手动上传蒙版
    let _saveImg = ``;
    const uploadBgi = document.getElementById('uploadMask')
    uploadBgi.click()
    uploadBgi.addEventListener('change', function onFileInputChange(e) {
        e.preventDefault()
        const files = e.target.files[0]
        const fileURL = URL.createObjectURL(files);
        convertToBase64(fileURL, function (base64Img) {
            keyDataArr[idx].mask = base64Img;
            _saveImg += `
            <img src="${base64Img}" style="position:absolute;z-index:2;width:300px;height:300px;border-radius:15px;"></img>
            `;
            $('#maskImg'+idx).append(_saveImg);
            $('.mask2').hide();
            uploadBgi.value = '' //去清空本次对话内容
            uploadBgi.removeEventListener('change', onFileInputChange);
            URL.revokeObjectURL(fileURL);
        });
    })
}

const renderVideo = (data,idx) => {
    let _videoItemHtml = ''
    for (let i = 0; i < data.length; i++) {
        _videoItemHtml += `
            <video id="video" controls src="${infoArr[i]}" style="position:absolute;z-index:2;width:300px;height:300px;border-radius:15px;"></video>
        `;
    }
    $('#vedio'+idx).append(_videoItemHtml)
    $('.mask').hide()
}
const renderToImage = (data,idx) => {
    $.ajax({
        type: 'POST',
        url: 'http://192.168.0.115:8000/video',//端口为8000的接口就是bimarsh的服务器的接口 //
        data: data,
        contentType: false,
        processData: false,
        success: function (res) {
            let words = res.trigger_words;
            keyDataArr[idx].prompt = words; //获取关键字
            console.log("keyData.prompt = ", words);
        },
        error: function (err) {
            console.log(err)
        }
    })
}
const wordToImg = (idx) => { //这里负责接收从图生图接口返回的数据
    $.ajax({
        type: 'post',
        url: 'http://39.170.83.107:7860/sdapi/v1/img2img',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(keyDataArr[idx]),
        success: function (data) {
            $('#getResult'+idx).empty(); //clear children nodes
            data.images.forEach(function (image) {
                let _capImg = `
                  <img src="data:image/png;base64,${image}" style="width:100%;height:auto;border-radius:15px;"></img>
                `;
                $('#getResult'+idx).append(_capImg);
                $('.progress').hide();
            });
        },
        error: function (err) {
            console.log('error', err)
        }
    })
}

//下面这个是假进度条，没啥大用，不影响程序主要逻辑运行
const totalTime = 60; // 定义总进度时间（秒）
// const numSteps = data.images.length; // 根据图像数量计算总步数
let currentStep = 0; // 当前步数
let currentWidth = 0; // 当前进度条的宽度
let stepIncrease = Math.floor(totalTime / 60); // 每步增加的时间
function updateProgress() {
    if (currentStep < 5) {
        currentStep++;
        currentWidth += 100 / 5;
        // 更新进度条的宽度，例如：
        $('.progress').show()

        $('.progressBar').css('width', `${currentWidth.toFixed(2)}%`);

        // 更新显示百分比，例如：
        // $('.progress').text(`${currentWidth.toFixed(2)}%`);
    }
}



/* from Tianshu */
trainIndex = 1;
function addTrainSession() { // 新增_训练进程 (UI加'我的进程 2'面板)
    trainIndex++;
    var container  = $('.content');
    const showSectionId = 'showSection' + trainIndex;
    const newContent = `
        <div class="showArea" id="${showSectionId}">
            <div class="areaTitleOfBackground">
                <div class="sesionInfo">我的视频 ${trainIndex}</div>
                <select class="dropdownSelect" id="dropdown${trainIndex}" onclick="onClickDropDown(${trainIndex})">
                    <option hidden disabled selected value>select an option</option>
                </select> <!--下拉菜单 -->
                <div class="spacer"></div> <!-- 用来占位 把下拉菜单 往前推 -->
                <div class="uploadInfo">
                    <div class="uploadImg" onclick="onRetrain(${trainIndex})" style="background-color:#8B0000;color:antiquewhite">
                                                                 重新训练</div>
                    <div class="uploadImg" onclick="wordToImg(${trainIndex})">获取结果</div>
                </div>
            </div>
            <div class="vedioContain">
                <div class="vedio" id="vedio${trainIndex}">
                    <div class="uploadVedio" onclick="uploadVedio(${trainIndex})">
                        <img src="icon/添加-方-L.png">
                        <p>上传视频</p>
                    </div>
                </div>
                <div style="margin: 0 20px 0 20px;"><img src="./icon/加.png"></div>
                <div class="img" id="img${trainIndex}">
                    <div class="uploadVedio" onclick="uploadImg(${trainIndex})">
                        <img src="icon/添加-方-L.png">
                        <p>上传图片</p>
                    </div>
                </div>
                <div style="margin: 0 20px 0 20px;"><img src="./icon/加.png"></div>
                <div class="maskImg" id="maskImg${trainIndex}">
                    <div class="uploadVedio" onclick="uploadMaskImg(${trainIndex})">
                        <img src="icon/添加-方-L.png">
                        <p>上传蒙版</p>
                    </div>
                </div>
                <div><img src="./icon/等于.png"></div>
                <div class="getImg" id="getResult${trainIndex}"></div> <!-- 结果图片 4宫格 -->
            </div>
        </div>
    `;
    container.append(newContent);
    keyDataArr.push(JSON.parse(JSON.stringify(keyData)));
    requestTrainedModels(); // 更新所有下拉列表 .dropdownSelect

    /* 结果图片4宫格_弹出大图 */
    var $modal    = $('#imageModal');
    var $modalImg = $("#modalImage");
    $('.getImg').on('click', 'img', function() {
        $modal.css('display', 'block');
        $modalImg.attr('src', $(this).attr('src'));
    });
    $('.close').on('click', function() {
        $modal.css('display', 'none');
    });
}
function onRetrain(idx) { // 清空视频、背景图片、蒙版 准备重新训练
    $('#vedio'  +idx)   .children(':not(:first)').remove();
    $('#img'    +idx)   .children(':not(:first)').remove();
    $('#maskImg'+idx)   .children(':not(:first)').remove();
    $('#getResult'+idx) .empty(); //clear children nodes
    $('#dropdown'+idx+' option:first').prop('selected', true);
    keyDataArr[idx].prompt = ''; // reset prompt
}
function renameKey ( obj, oldKey, newKey ) {
    obj[newKey] = obj[oldKey];
    delete obj[oldKey];
}
function requestTrainedModels() { // 收取已训练的 model/prompt 列表
    $.ajax({
        type:'GET',
        url:'http://192.168.0.115:8000/refresh',
        contentType: false,
        processData: false,
        headers: {
            'Accept': 'application/json'
        },
        success:function (res) {
            optArr = JSON.parse(JSON.stringify(res));
            optArr.forEach( obj => renameKey( obj, 'prompt', 'value' ) );
            let selectOptions = $.isEmptyObject(optArr) ? [
                { name: "Option 1", value: "1" },
                { name: "Option 2", value: "2" },
                { name: "Option 3", value: "3" }
            ] : optArr;
            /* Populate dropdown list */
            let $dropdownSelect = $('.dropdownSelect');
            $.each(selectOptions, function(index, option) {
                $dropdownSelect.append(
                    $('<option>').text(option.name).val(option.value)
                );
            });
        },
        error: function(xhr, status, error) {
            console.log('Error:', error);
        }
    });
}
function onClickDropDown(idx) {
    const dropdown = $('#dropdown'+idx)[0];
    dropdown.click();
    dropdown.addEventListener('change', function onOptionChange(e) {
        e.preventDefault()
        const optionName = $(this).find('option:selected').text();
        const optionValue= $(this).val();
        const videoId = '#vedio' + idx;
        $(videoId).children(':not(:first)').remove();
        keyDataArr[idx].prompt = optionValue; // 注意！！！！ 这里要确定 下拉菜单选项按钮 要激活(idx)
        let _optPrompt = `
            <div class="prompt"><br><br><br>name: `+optionName+`<br>promt: `+optionValue+`</div>
        `;
        $(videoId).append(_optPrompt);
        dropdown.removeEventListener('change', onOptionChange);
    });
}
$(document).ready(function() { //vxa,aok,a stuffed doll <lora:doll:0.5> <lora:video(1):0.5>
    requestTrainedModels();
    /* Bind the change evnt to dropdown */

        // $('.content').on('change', '.dropdownSelect', function onOptionChange() {
        //     const optionName = $(this).find('option:selected').text();
        //     const optionValue= $(this).val();
        //     const index = $(this).data('index');
        //     const videoId = '#vedio' + index;
        //     $(videoId).children(':not(:first)').remove();
        //     keyDataArr[index].prompt = optionValue; // 注意！！！！ 这里要确定 下拉菜单选项按钮 要激活(idx)
        //     let _optPrompt = `
        //         <div class="prompt"><br><br><br>name: `+optionName+`<br>promt: `+optionValue+`</div>
        //     `;
        //     $(videoId).append(_optPrompt);
        //     $('#dropdown'+index).removeEventListener('change', onOptionChange);
        // });
});

/* 结果图片4宫格_弹出大图 */
var $modal    = $('#imageModal');
var $modalImg = $("#modalImage");
$('.getImg').on('click', 'img', function() {
    $modal.css('display', 'block');
    $modalImg.attr('src', $(this).attr('src'));
});
$('.close').on('click', function() {
    $modal.css('display', 'none');
});
/* 备用方案 - remove.bg API 背景消除 */
function uploadVideo(res) { //上传视频
    const uploadVedio = document.getElementById('uploadVedio');
    uploadVedio.click();
    uploadVedio.addEventListener('change', function (file) {
        file.preventDefault()
        const files = file.target.files[0]
        const fileURL = URL.createObjectURL(files);
        infoArr.push(fileURL)
        renderVideo(infoArr)

        var $video = $('#video');
        $video.attr('src', fileURL);

        $video.on('loadeddata', function() {
            // Set the time of the frame you want to capture (in seconds)
            this.currentTime = 5; // For example, capture frame at 5 seconds
        }); // 回头改成  取4张 每个5秒/几秒 取一张 this.maxTime/4

        $video.on('seeked', function() {
            var canvas = $('<canvas>')[0];
            canvas.width = this.videoWidth;
            canvas.height = this.videoHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(this, 0, 0, canvas.width, canvas.height);

            // Convert to base64
            var base64Image = canvas.toDataURL('image/png');
            removeBg(base64Image);
            
            // Clean up
            URL.revokeObjectURL(fileURL);
        });

        uploadVedio.value = '' //去清空本次对话内容
    });
}
function removeBg(base64) { // 去除背景 抠好的图_放在结果栏
    var api_key = 'wcwHNQX6DwzcsgBWPU3WqpS1';
        var base64ImageContent = base64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
        var formData = new FormData();
        formData.append('image_file_b64', base64ImageContent);
        formData.append('size', 'auto');

        $.ajax({
            url: 'https://api.remove.bg/v1.0/removebg',
            type: 'POST',
            data: formData,
            headers: {
                'X-Api-Key': api_key,
                'Accept': 'application/json'
            },
            contentType: false,
            processData: false,
            success: function(response) {
                let _saveImg = `
                <img src="data:image/png;base64,${response.data.result_b64}" style="position:absolute;z-index:3;width:100px;height:auto;bottom:-50px;right:0px;border-radius:15px;"></img>
                `;
                $('.getImg').append(_saveImg);
            },
            error: function(xhr, status, error) {
                console.error("Error:", status, error);
            }
        });
}
function wrdToImg() { // 背景图片 放入结果栏
    const _saveImg = `
    <img src="${keyData.init_images[0]}" style="position:absolute;z-index:2;width:300px;height:300px;border-radius:15px;"></img>
    `;
    $('.getImg').append(_saveImg);
}

