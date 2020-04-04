from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template import loader
from .forms import PhotoForm
from .models import Photo, Kakugen, Talk
from . import forms
from django.template.context_processors import csrf

# ホーム画面を表示
def home(request):
    template = loader.get_template('home.html')
    return render(request, 'home.html')

# リスト画面を表示
def list(request):
    template = loader.get_template('list.html')
    return render(request, 'list.html')

# 自己紹介画面を表示
def introduction(request):
    template = loader.get_template('introduction.html')
    return render(request, 'introduction.html')

# リスト画面に戻る
def back(request):
    return redirect ('list')

# 未完成画面を表示
def wait(request):
    template = loader.get_template('wait.html')
    return render(request, 'wait.html')

# 顔診断準備画面を表示
def facejudge(request):
    template = loader.get_template('facejudge.html')
    context = {'form':PhotoForm()}
    return HttpResponse(template.render(context, request))

# 顔診断結果画面を表示
def predict(request):
    if not request.method == 'POST':
        return redirect('facejudge')

    form = PhotoForm(request.POST, request.FILES)
    if not form.is_valid():
        raise ValueError('Formが不正です')

    photo = Photo(image=form.cleaned_data['image'])
    predicted, percentage = photo.predict()

    template = loader.get_template('dcmresult.html')

    context = {
        'photo_name' : photo.image.name,
        'photo_data' : photo.image_src(),
        'predicted' : predicted,
        'percentage' : percentage,
    }
    return HttpResponse(template.render(context, request))

# 格言生成準備画面を表示
def kakugen(request):
    template = loader.get_template('kakugen.html')
    return render(request, 'kakugen.html')

# 格言生成結果画面を表示
def kakugen_result(request):

    # 格言クラスの読み込み
    kakugen = Kakugen()
    # 格言生成
    sentence = kakugen.make_kakugen()

    template = loader.get_template('kakugen_result.html')

    context = {
        'sentence' : sentence,
    }

    return HttpResponse(template.render(context, request))

# 応答用の辞書を組み立てて返す
def __makedic(k, txt):
    return {'k': k, 'txt': txt}

#チャットボット生成画面
def talk_do(request):
    t = Talk()
    if request.method == 'POST':
        # テキストボックスに入力されたメッセージ
        q = request.POST["texttwo"]
        # 応答メッセージ取得
        a = t.respond(q)
        # 描画用リストに最新のメッセージを格納する
        talktxts = []
        talktxts.append(__makedic('ai', a))
        talktxts.append(__makedic('b', q))
        # 過去の応答履歴をセッションから取り出してリストに追記する
        saveh = []
        if 'hist' in request.session:
            hists = request.session['hist']
            saveh = hists
            for h in reversed(hists):
                x = h.split(':')
                talktxts.append(__makedic(x[0], x[1]))
        # 最新のメッセージを履歴に加えてセッションに保存する
        saveh.append('b:' + q)
        saveh.append('ai:' + a)
        request.session['hist'] = saveh
        # 描画準備
        form = forms.UserForm(label_suffix='：')
        c = {
            'form': form,
            'texttwo': '',
            'talktxts': talktxts
        }
    else:
        # 初期表示の時にセッションもクリアする
        request.session.clear()
        # フォームの初期化
        form = forms.UserForm(label_suffix='：')
        c = {'form': form}
        c.update(csrf(request))
    return render(request, 'chatbot.html', c)