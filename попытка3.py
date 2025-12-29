import os
import json
import re
from flask import Flask, request, jsonify
from datetime import datetime
import logging
import gspread
from google.oauth2.service_account import Credentials
from threading import Lock

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = '1-7tesS_fvz_Kk9ZkWCPsZfT5uyBu3hgwbImqMylFbeI'  # Из UR

SHEET_NAMES = {
    'warehouse': 'Брак Склада',
    'production': 'Производство'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

WEBHOOK_TOKEN = "token20220705"
PORT = 8000
BIND_HOST = "0.0.0.0"

lock = Lock()

PRODUCTS = ["Примадофилус_порошок","Пантовигар_Лосьон_Муж","STZ_Agenta_Aжента_100","PML_PML_Завтрак_200","PML_PML_Хлорофил_500","Велкид","Кальцимакс","Велмен_Трихолоджикк","Велвумен_Энерджи","Велзим","Aquamarine","Pregnacare","VTB_Krasavit_Красавит_30","Perfectil_Platinum_60","Perfectil_Platinum_30","Wellwoman Plus","Менопейс","Wellwoman 50+","Wellman plus","wellwoman","Menopause","Feroglobin","Перфектил Плюс","Велбио","Перфектил_Трихолоджик","перфектил 01","Аспепта_Витамины","Флексиново","KeloCote_6g","Microlet ланцеты","Вобэкэа","Максилак_Экспресс","Ультра-Д_720","Биогая_Табл_20","Ультра-Д_360","Примадофилус_50г","Биогая_Капли_ВитD3","Пантовигар_Лосьон_Муж","Пантопровит_60","Максилак Бэби","Примадофилус_90 капсул","Максилак_Бэби_Капли","KeloCote_15g","Ультра-Д_120","Саугелла_Аттива","Саугелла_Полиджин","Ecoderm","Regecin_Krem","САУГЕЛЛА для девочек","SHB_Dr.Ohhira_Коллаген_10","SHB_Dr.Ohhira_РастительныйКомплекс_120","SHB_Dr.Ohhira_Коллаген_15","SHB_Dr.Ohhira_РастительныйПреметабиотик_30","SHB_Dr.Ohhira_РастительныйКомплекс_60","NOX_NOX_Прокладки_6","KSM_kosmoteros_СывВитКомп_30","KSM_Kosmoteros_ТоникНорм_200","KSM_kosmoteros_Тониксух_200","KSM_kosmoteros_Тоникжир_200","KSM_kosmoteros_ТоникВитС_200","KSM_ГельПенкаМат_150","KSM_ГельПенкаBG_150","KSM_kosmoteros_ГельAHA_200мл","KSM_kosmoteros_ГельВсеТипыКожи_200","KSM_kosmoteros_себорегулятор_50","KSM_kosmoteros_крем15spf_50","KSM_kosmoteros_КонцАнтиЭйджРевит_30","KSM_kosmoteros_КонцЛифт_30","KSM_kosmoteros_КонцСуперУвлаж_30","KSM_kosmoteros_КонцЭластКожа_30","KSM_kosmoteros_КонцГлик_30","PML_PML_Хлорофил_100","ESC_serum_acne_30","ESC_serum_vitA_30","ESC_serum_vitC_30","ESC_mask_lifting_50","KSM_kosmoteros_КремИкра_25","KSM_kosmoteros_КремSL_25","KSM_kosmoteros_КремВитС_50","KSM_kosmoteros_КремСПФ30_50","KSM_kosmoteros_Ремодулятор_30","KSM_kosmoteros_кремIB_50","KSM_kosmoteros_крембриллиант_50","KSM_Kosmoteros_МаскаШокУдов_10","KSM_Kosmoteros_МаскаЭнзимПил_10","KSM_Kosmoteros_МаскаНежныеСливки_50","KSM_Kosmoteros_МаскаВекиHYASEALON_1","KSM_Kosmoteros_МаскаЭкспрессЛифтинг_50","KSM_Kosmoteros_МаскаИммунокор_50","KSM_Kosmoteros_МаскаСеборег_50","KSM_Kosmoteros_МаскаBeauteGlobale_50","KSM_Kosmoteros_МаскаМорКоллаген_50","KSM_Kosmoteros_ПилингГоммаж_50","KSM_Kosmoteros_ЛосьонГидроактиватор_200","KSM_Kosmoteros_КремМорКоллаген_50","KSM_Kosmoteros_ЛосьонБиоактиватор_200","KSM_Kosmoteros_КремSuperGold_80","KSM_Kosmoteros_ГельAnticouperose_50","QTX_Qtix_Размягчитель_15","QTX_Qtix_Праймер_15","QTX_Qtix_КаучукБазаСуперСцепка_15","QTX_Qtix_УниверКремОсвежКлуб_150","QTX_Qtix_ТопDiamondБезЛипСлой_8","QTX_Qtix_ЖидкийПолигельПрозрач_15","QTX_Qtix_Монарда_15","Nox_Nox_ПрокладкиXSS_6","AFP_AFP_Ф8Псоризан_90","AFP_AFP_Ф9Куперозан_75","AFP_AFP_КремФитофлорис_200","AFP_AFP_КремПапилФит_5","AFP_AFP_КоллагенВитС_120","AFP_AFP_ЭкстрЕжов_60","AFP_AFP_ЭкстрЛопух_60","RCL_COLLAGEN_СкрабPreamur_500","RCL_COLLAGEN_СкрабPreamur_250","RCL_COLLAGEN_ГельАнтицелLIGHT_500","RCL_COLLAGEN_МагниевоеМасло_250","RCL_COLLAGEN_СывороткаАктиватор_250","RCL_COLLAGEN_МаслоМассажАнтицел_500","RCL_COLLAGEN_КремМолочко_500","SHB_Dr.Ohhira_РастительныйКомплекс_30","ESC_EverEco_кремспф30_30","ESC_EverEco_сывороткавитамины_30","ESC_EverEco_сывороткатерминалия_15","ESC_EverEco_сывороткаколлаген_30","ESC_EverEco_сывороткамаслоретинол_30","ESC_EverEco_тоникАнтиакне_100","ESC_EverEco_тониквитС_100","ESC_EverEco_маскаретинол_50","ALF_Alfit_ФитосборМастопатия_60","ALF_Alfit_ФитосборГинекология_60","ALF_Alfit_ФитосвечиПростозол_15","ALF_Alfit_ФитосвечиГинекозол_15","ESC_EverEco_скрабкедр_50","ALF_Alfit_ФитосборДляСниженияВеса_60","ALF_Alfit_ФитосборДляЖКТ_60","ALF_Alfit_ФитосборДляМозговогоКровообращения_60","ALF_Alfit_ФитосборДляПечени_60","ALF_Alfit_ФитосборПротивопаразитный_60","ALF_Alfit_ФитосборДляНормализацииСахара_60","ALF_Alfit_ФитосборДляИммуннойСистемы_60","ALF_Alfit_ФитосборКлимактерический_60","ALF_Alfit_КапсулыГинеконорм_60","ALF_Alfit_КапсулыМастонорм_60","ALF_Alfit_ПанталфитМужской_30","ALF_Alfit_Лисички_30","ALF_Alfit_ЧагаРейше_30","FMT_Ecoderm_Шампунь_150","FMT_Regecin_Гель_15","FMT_Sebozol_Шампунь_100","FMT_Sebozol_Шампунь_200","FMT_MagniyFT_МагнийB6_50","FMT_ShalfeyFT_Шалфей_20","FMT_AquaFoeniculi_УкропнаяВода_15","VTB_Perfectil_HairCrush_60","VTB_Menopace_Менопейс_30","VTB_Pregnacare_Прегнакеар_28&28","VTB_Wellman_Таблетки_30","VTB_Calcimax_Кальцимакс_60","VTB_Krasavit_Красавит_30","VTB_Wellkid_Велкид_30","VTB_Perfectil_Таблетки_30","VTB_Perfectil_Трихолоджик_60","VTB_Feroglobin_Фероглобин_30","VTB_Perfectil_Платинум_30","VTB_Wellman_Трихолоджик_60","VTB_Wellwoman_50+_30","VTB_Wellwoman_Плюс_28&28","VTB_Wellwoman_30+_30","VTB_Menopace_Плюс_28&28","VTB_Wellman_Плюс_28&28","VTB_Aquamarin_Аквамарин_60","VTB_Perfectil_Платинум_60","VTB_Wellbio_Велбио_30","VTB_Wellwoman_Энерджи_10","VTB_Wellman_Энерджи_10","QTX_Qtix_Монарда_15","QTX_Qtix_Размягчитель_15","RDM_Readyme_Маска_150","COB_Cocobrico_уголь22_96","QTX_Qtix_МаслоКлубника_15","QTX_Qtix_Праймер_15","QTX_Qtix_МатовыйТоп_15","COB_Cocobrico_уголь25_84","ADR_Адрилан_СпрейАкрил_500","ADR_Адрилан_СпрейАнтиК_500","ADR_Адрилан_СпрейУни_500","ADR_Адрилан_ГельЦветы_850","ADR_Адрилан_ГельЛимон_850","ADR_Адрилан_ГельФрукты_850","ADR_Адрилан_ГельЦветы_5","FMT_Sebozol_Шампунь_25","LTM_Vitaon_БальзамЛюкс_25","VTB_Cardioace_Кардиоэйс_30","VTB_Jointace_Омега3_30","PLS_Admera_Крем_150","PLS_Admera_Крем_50","PLS_Отофаг_Гель_50","PLS_Alerana_Алерана_60","PLS_Мексидол_Паста_100","APH_Aphrodite_КремРукиАвокадоРомашка_150","APH_Aphrodite_КремРукиАлоэ_150","APH_Aphrodite_КремГлазаКоэнзQ10_30","APH_Aphrodite_КремЛицоОмолаж_50","APH_Aphrodite_КремЛицоМатир_50","APH_Aphrodite_КремCC_50","PLS_Суперчистотело_Маркер_5","GLP_КремПодгузн_75","FMT_AquaFoeniculi_УкропнаяВодаСаше_10","UNL_Axe_ГифтПакШампГддДезDT_600","UNL_Axe_ГельШампуньФеникс_610","UNL_Axe_ГельШампуньANTI_HANGOVER_610","FMT_Ecoderm_Шампунь_750","SHB_Dr.Ohhira_Коллаген_10","SHB_Dr.Ohhira_Коллаген_15","SHB_Dr.Ohhira_РастительныйКомплекс_120","SHB_Dr.Ohhira_РастительныйКомплекс_60","SHB_Dr.Ohhira_РастительныйПреметабиотик_30","SHB_Dr.Ohhira_РастительныйКомплекс_30","UNL_Axe_ШампуньГельCoolOcean_610","UNL_Axe_ГельШампуньEPIC_FRESH_610","UNL_Axe_ГельШампуньНаПляже_610","UNL_Axe_ГельКожаПеченьки_610","UNL_Axe_ГельDarkTemptation_610","UNL_Axe_ГельIceChill_610","UNL_Axe_ГельШампуньАкватическийБергамот_400","UNL_Axe_ГельСилаДжунглей_610","UNL_Axe_ГельСилаТехнологий_610","UNL_Axe_ГельИзумрудныйПачули_400","UNL_Axe_ГельМедныйСандал _400","UNL_Axe_ГельШампуньЯнтарноеМанго_400","UNL_Axe_ДезодорантАкватическийБергамот_150","UNL_Axe_ДезодорантИзумрудныйПачули_150","UNL_Axe_ДезодорантМедныйСандал_150","UNL_Axe_ДезодорантЯнтарноеМанго_150","UNL_Axe_ДезСтикDarkT_50","UNL_Axe_НаборГддДезDT_250","UNL_Axe_ГифтУдача_400","UNL_Camay_ГельВосхитительноеОчарование_750","UNL_Camay_ГельГипнотическаяАура_750","UNL_Camay_ГельМагическоеЗаклинание_750","UNL_Camay_МистПионЯгоды_115","UNL_Camay_НаборГелей_2х250","UNL_Camay_НаборГддМочалка_250","UNL_Camay_ГельТайноеБлаженство_750","UNL_Cif_НаборАПАНАЖ_1500","UNL_Cif_СпрейАнтижир_500","UNL_Cif_СпрейКремПена_500","UNL_Clear_CDEШампуньДляРоста_380","UNL_Clear_CDEШампуньОтПерхоти_380","UNL_Clear_CDEСывороткаДляВолос_190","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","UNL_Clear_CDTСкрабДляВолосЭР_150","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","UNL_Clear_ШапуньБальзамMen_610","UNL_Clear_ГельШампуньБальзамMen_610","UNL_Clear_ШампуньОтВыпаденияВолос_610","UNL_Clear_ПилингДляГоловы_150","UNL_CrystalPur_ГельОчищ_190","UNL_CrystalPur_ГидрофильноеМасло_110","UNL_Dove_КремКокос_300","UNL_Dove_КремГельПитаниеУвлажнение_610","UNL_Dove_КремГельИнжирАпельсин_610","UNL_Dove_КремГельФисташковыйКрем_610","UNL_Dove_НаборСухойШампунь_500","UNL_Dove_ГифтПакШампГдд_500","UNL_Dove_НаборКремДляРукДез_100    ","UNL_Dove_ШампБальзЛаванда_1260","UNL_Dove_ШампБальзМанго_1260","UNL_Dove_ШампБальзВосст_1260","UNL_Feel Moment_ГидроБальзам_45","UNL_Feel Moment_КремРетинол_50","UNL_Feel Moment_КремЦинкНиацин_50","UNL_Feel Moment_ПенкаДляЛица_190","UNL_Feel Moment_СывороткаВитС_30","UNL_Feel Moment_СывороткаРетинол_30","UNL_Rexona_ГддМужГорныйЛед_750","UNL_Rexona_НаборMenГддДез_230","UNL_Rexona_ГифтПакДезГдд23_330","UNL_Rexona_НаборГддДезПляж_240","UNL_Rexona_ДезКдрСердце_95","UNL_Tresemme_ШампуньБальзамКремВолны_880","UNL_Tresemme_БальзамКератин_930","UNL_Tresemme_ШампуньБальзамКератин_1930","UNL_Tresemme_ШампуньКератин_1000","UNL_Tresemme_МаскаДляВолосRep_300","UNL_Tresemme_МаскаДляВолосRichM_300","UNL_Tresemme_МаскаДляВолосОкраш_300","UNL_Tresemme_МаслоДляВолосRep_50","UNL_Tresemme_МуссДляВолос5Фикс_200","UNL_Tresemme_МуссДляВолос3Объем_200","FMT_AquaFoeniculi_УкропнаяВода_15","UNL_Tresemme_НаборСухойШампунь_500","UNL_Tresemme_НаборШампуньСпрей_420","UNL_Tresemme_СпрейДляВолос_190","UNL_Tresemme_СпрейДляВолосОбъемBFV_190","UNL_Tresemme_СывороткаФлюидRichM_190","UNL_Tresemme_ШампуньБальзам_1280","UNL_Tresemme_ШампуньБальзамОбъем_1280","UNL_Tresemme_ШампуньБальзамОкраш_1280","UNL_Tresemme_ШампуньБальзамУвлажнение_800","UNL_Tresemme_ШампуньБальзамДетокс_800","UNL_Tresemme_ШампуньБальзамБриллиант_800","UNL_Tresemme_ШампуньБальзамКератин_800","UNL_Tresemme_ШампуньБальзамRP_800","UNL_Tresemme_ШампуньБальзамОбъем_800","UNL_Tresemme_ШампуньБальзамОкраш_800","UNL_Tresemme_ШампуньБальзамВолны_800","UNL_Tresemme_ШампуньБальзамУвлажнение_1280","UNL_Бархатные ручки _ЖидкоеМылоПак_1000","UNL_Бархатные ручки _ЖидкоеКремМыло_5","UNL_Бархатные ручки_НаборКремов_90","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_КремСкульптор_50","FMT_AquaFoeniculi_УкропнаяВодаСаше10","UNL_Лесной бальзам_ЗПОтбелХЗ_319","UNL_Лесной бальзам_ЗубнаяПастаTotal_290","UNL_Лесной бальзам_НаборСольИМятаДоз_580","UNL_ЧернЖем_КремСкульптор_50","SHB_Dr.Ohhira_РастительныйКомплексDeLuxe_30","UNL_ЧернЖем_ПилингСкатка_120","UNL_Черный жемчуг_БазаПодМакияжСПФ_40","UNL_Черный жемчуг_ГельПилинг_80","UNL_ЧернЖем_КремСкульптор_50","UNL_ЧернЖем_AntiAgeКремSPF30_48","UNL_Черный жемчуг_КремФиллерДневной_48","UNL_ЧернЖем_КремСкульптор_50","UNL_Черный жемчуг_КремДляВек_15","UNL_Черный жемчуг_МицеллВода_750","UNL_Черный жемчуг_МистПитание_115","UNL_Черный жемчуг_МистУвлажнение_115","UNL_Черный жемчуг_МультиКремБальз_50","UNL_Черный жемчуг_МультиКремДляВек_40","UNL_Черный жемчуг_СтикДляГуб_12","UNL_ЧернЖем_НочнКремМаскаLift_48","UNL_Черный жемчуг_ПилингМаскаОбнов_81","UNL_Черный жемчуг_СплэшМаска_160","UNL_Черный жемчуг_МультиСДСС_170","UNL_ЧернЖем_КремСкульптор_50","UNL_Черный жемчуг_СывороткаБустерВосстанавл_30","UNL_Черный жемчуг_СывороткаБустер_30","UNL_Черный жемчуг_СывороткаБустерРазглаж_30","UNL_ЧернЖем_КремСкульптор_50","UNL_Черный жемчуг_СывороткаБустерУкрепл_30","UNL_Черный жемчуг_СывороткаБустерУспокающ_30","UNL_Черный жемчуг_МультиКремТело_150","UNL_ЧистаяЛиния_ГельПерсик_750","UNL_ЧистаяЛиния_ГельПробуждающий_750","UNL_ЧистаяЛиния_ГельКлубника_750","UNL_ЧистаяЛиния_МицеллВода_750","VTB_Wellwoman_Плюс_28&28","VTB_Wellman_Плюс_28&28","VTB_Perfectil_Плюс_28&28","GRT_HealthIs_ЖелезоСульфат_60","GRT_HealthIs_ЖелезоСульфат_60","GRT_HealthIs_ЛецитинПодсолн_120","GRT_Handy_МаслоМонарды_30","GRT_HealthIs_МагнийB6_30","GRT_HealthIs_МагнийВ6_V.2","GRT_HealthIs_Куркумин_30","GRT_HealthIs_Дигидрокверцетин_30","GRT_HealthIs_Таурин_90","GRT_Handy_Ремувер_30","GRT_HealthIs_Биотин_60","GRT_HealthIs_Женьшень_60","GRT_HealthIs_Хром_60","GRT_HealthIs_Йод_60","GRT_HealthIs_МагнийB6_30*3","GRT_HealthIs_КореньЛопуха_60","GRT_Handy_МаслоЧайногоДерева_30","GRT_HealthIs_АльфаЛипКислота_60","GRT_HealthIs_Тирозин_60_","GRT_HealthIs_Д3_180","GRT_HealthIs_Глицин_60","GRT_HealthIs_Спирулина_90","GRT_HealthIs_Расторопша_1000_120","GRT_HealthIs_КоэнзимQ10_100_60","GRT_HealthIs_ЕжовикГребенчатый_2000_120","GRT_HealthIs_Селен_150_60","GRT_HealthIs_ФолиеваяКислота_600_180","GRT_HealthIs_Таурин_90","GRT_HealthIs_МагнийХелатВ6_120","GRT_HealthIs_В-Комплекс_60","GRT_Handy_КремОтРастяжек_250","GRT_HealthIs_Д3'5000_180","GRT_HealthIs_ЦинкПиколинат_120","GRT_HealthIs_ВитаминА_10000_90","GRT_HealthIs_ВитаминЕ_60","GRT_HealthIs_Хлорофилл_500","GRT_HealthIs_Берберин_60","GRT_HealthIs_ДетскиеВитамины_60","GRT_Handy_НаборМонардаРемувер_60","GRT_Handy_МаслоУсьмы_10","GRT_HealthIs_Астаксантин_90","GRT_HealthIs_Габа_90","GRT_HealthIs_Карнитин_90","GRT_HealthIs_Коллаген_90","GRT_HealthIs_Глицин_90","GRT_HealthIs_5-htp_60","GRT_HealthIs_Пробиотики_60","GRT_HealthIs_ZMA_120","GRT_HealthIs_КоллагенПорошок_30","GRT_HealthIs_ЯнтарнаяКислота_120","GRT_Handy_МаслоДляКутикулыИНогтей_30","GRT_Handy_МаслоДляЛицаМассажное_30","GRT_HealthIs_Омега3_180","GRT_HealthIs_Глюкозамин_90","GRT_HealthIs_МужскиеВитамины_60","GRT_HealthIs_ЖенскиеВитамины_60","GRT_HealthIs_ВитаминС_120","GRT_Handy_МассажноеМаслоДляТела_500","GRT_Handy_МаслоДляВолос_100","GRT_HealthIs_Инозитол_60","GRT_Handy_МаслоШи_150","GRT_Handy_МаслоРозмарина_30","GRT_HealthIs_Хром_120","GRT_HealthIs_Набор_4","GRT_HealthIs_Д3К2_120","GRT_Handy_МагниевоеМасло_200","GRT_HealthIs_ЖелезоХелат_60","GRT_HealthIs_Лецитин2000_120","KSM_kosmoteros_КремСПФ50_50","SHB_Dr.Ohhira_РастительныйКомплексDeLuxe_60","GRT_HealthIs_МагнийЦитрат_120","GRT_HealthIs_ГлицинДляДетей_60","GRT_HealthIs_ВитаминыДляВолос_60","UNL_ЧистаяЛиния_ГддКдрMen_330","UNL_Чистая Линия_НаборМульти_200","UNL_PureLine_СывороткаКоррект_30","UNL_PureLine_КремОтПрыщей_185","UNL_PureLine_КриоГель_45","UNL_PureLine_КриоПатчиДляВек_30","UNL_PureLine_ПенкаОтПрыщей_190","FMT_Regecin_НаборГель_30","GRT_HealthIs_Омега3_90","GRT_HealthIs_Омега369_180","UNL_CrystalPur_КремУвлажнЦерамиды_50","UNL_CrystalPur_СывороткаОмолаживающая_30","UNL_CrystalPur_СывороткаУвлажняющая_30","VTB_Pregnacare_Прегнакеар_28&28","GRT_HealthIs_К2_90","GRT_HealthIs_МаслоЧерногоТмина_90","UNL_Camay_ГельФранцузскаяРоза_750","UNL_Camay_ГельПенаЛавандаМагний_750","UNL_Camay_ГельЯпонскаяСакура_750","UNL_Camay_ГельРозовыйГрейпфрут_750","UNL_Camay_ГельВишняМиндаль_750","UNL_Camay_ГельГранатКоллаген_750","UNL_Camay_ГельЦитрусовыйМикс_750","UNL_Camay_ГельАбрикосМаслоШи_750","GRT_Handy_РемуверДляКутикулы_50","GRT_Handy_Крем-баттерДляТела_250","GRT_HealthIs_ЛипотропныйФактор_90","UNL_Dove_ШампБальзАвокадо_1260","UNL_Tresemme_НаборЛаков_500","UNL_ЧистаяЛиния_НаборПенок_300","UNL_Tresemme_СпрейДляВолосКератин_250","GRT_Healthis_МагнийЦитрат_240","GRT_HealthIs_МагнийХелатВ6_270","GRT_HealthIs_Глюкозамин_180","GRT_Kottur_МаслоДляЗагара_150","GRT_Kottur_КремСМочевиной_500","GRT_HealthIs_Креатин_300","Perfectil_Tricologic01","GRT_HealthIs_Коллаген_180","GRT_HealthIs_Куркумин_30","FMT_Sebozol_Шампунь_25","UNL_Camay_Набор2ГелейЗаклинаниеРоза_1500","UNL_Tresemme_ШампуньБальзамСпрейВосст_990","UNL_Tresemme_ШампуньБальзамМаскаВолны_920","GRT_Handy_НаборМаслоМонарды_60","GRT_Handy_НаборМаслоРозмарина_60","GRT_Kottur_СПФДляЛица_50","GRT_HealthIs_ЖелезоХелат_120","GRT_HealthIs_Аргинин_180","GRT_HealthIs_Д3К2_180","GRT_HealthIs_Д3К2_365","GRT_HealthIs_Аргинин_90","GRT_HealthIs_Цинк_60","GRT_HealthIs_Карнитин_500","GRT_Kottur_КремДляЛицаУвлажняющий_50","GRT_Kottur_КремВоск_100","GRT_Kottur_ПарфюмКремLostCherry_300","GRT_Kottur_ПарфюмКремTobaccoVanille_300","GRT_HealthIs_ЦинкСелен_90","GRT_HealthIs_НаборЖМ_2","GRT_HealthIs_КоллагенДляСуставов_240","GRT_HealthIs_ВитаминС_240","UNL_Camay_Набор2ГелейЗаклинаниеОчар_1500","UNL_Camay_Набор2ГелейРозаОчар_1500","GRT_HealthIs_МагнийЦитрат_240","GRT_HealthIs_Биотин_60_v2","GRT_HealthIs_Д3'5000_180_v2","GRT_HealthIs_КоллагенДляСуставов_120","GRT_HealthIs_В-Комплекс_120","GRT_HealthIs_Д3'600_180","GRT_Handy_НаборМаслоУсьмы_20","GRT_HealthIs_Берберин_60_v2","GRT_HealthIs_Д3_180_v2","GRT_HealthIs_Таурин_180","GRT_HealthIs_КоэнзимQ10_100_120","GRT_HealthIs_Д3'600_365","UNL_Dove_ГельШелкУвлажн_1220","UNL_Dove_ГельШелкПион_1220","UNL_DoveГельУвлажКрем_760","UNL_Dove_МолочкоГельУвлаж_810","UNL_Черный жемчуг_ПенкиНабор_300","UNL_Черный жемчуг_МультикремаНабор_86","UNL_Rexona_НаборГельУгольОкеан_980","UNL_Axe_НаборГельПеченьеDarkTemp_1220","UNL_Tresemme_НаборМаслоДляВолосRep_100","UNL_Черный жемчуг_НаборКремДляВек_30","UNL_Camay_НаборМистПионГельОчар940","UNL_Tresemme_НаборСпрейДляВолос_380","UNL_Tresemme_МаскаКератинДляВолос_500","UNL_CrystalPur_ЭнзимПудра_70","UNL_Dove_МолочкоВишня_280","UNL_Dove_КремБаттерМанго_300","UNL_Dove_КремКокосNew_300","UNL_Dove_ЛосьонЛаймКлубника_280","GRT_HealthIs_Лецитин2000_240","GRT_HealthIs_Глицин_180","GRT_HealthIs_ВитаминыДляВолос_120","GRT_HealthIs_НаборЖенский_3","GRT_HealthIs_Д3дляДетей_60","GRT_HealthIs_НаборМужской_3","GRT_HealthIs_Мультивитамины_60","GRT_HealthIs_КальцийД3_240","GRT_HealthIs_КальцийдляДетей_60","GRT_HealthIs_5-htp_120","UNL_Camay_Набор3ГелейМагРозаОчар_2250","GRT_HealthIs_ВитаминЕ_120","GRT_HealthIs_Инозитол_120","GRT_HealthIs_Мультивитамины_120","GRT_Kottur_ГельДляИнтимнойГигиены_500","GRT_HealthIs_НаборХлорофилл_2","GRT_HealthIs_НаборКарнитин_2","GRT_HealthIs_Селен_150_120","GRT_HealthIs_ВитаминСдляДетей_60","GRT_HealthIs_КарнитинЖидкийВишня_500","GRT_HealthIs_Астаксантин_180","GRT_HealthIs_Набор_4","GRT_HealthIs_Биотин150_90","GRT_HealthIs_Биотин150_180","GRT_Kottur_НаборКремыLostСherryTobaccoVanille_600","GRT_HealthIs_АльфаЛипКислота_120","GRT_HealthIs_КарнитинЖидкийЯблоко_500","GRT_HealthIs_ZMA_180","GRT_HealthIs_ZMA_120","GRT_HealthIs_Омега369_90","GRT_HealthIs_ВитаминС_120","GRT_HealthIs_МагнийЦитрат_120","GRT_HealthIs_МагнийЦитрат_240","GRT_HealthIs_ВитаминС_240","UNL_Camay_ГифтМистГддDesir_440","UNL_Camay_НаборГелейNEW_2х250","UNL_Axe_ГифтМедведьDT_250","UNL_Axe_ГифтПопугайEF_300","UNL_Clear_ГифтDermaTherapy_1020","UNL_Rexona_ГифтКдрДезСердце_95","UNL_Rexona_ГифтMenГддДезNEW_230","UNL_Rexona_ГифтЦитрусNEW_240","UNL_Tresemme_ГифтКосметичка_215","UNL_Tresemme_ГифтВосстШБ_460","UNL_Черный жемчуг_ГифтМЦКрем_296","AFP_AFP_КремПапилФит_5","vtb_krasavit_красавитплюс_30","KSM_Kosmoteros_ТоникНорм_200","KSM_kosmoteros_Тониксух_200","KSM_kosmoteros_Тоникжир_200","KSM_kosmoteros_ТоникВитС_200","KSM_ГельПенкаМат_150","KSM_ГельПенкаBG_150","KSM_kosmoteros_ГельAHA_200мл","KSM_kosmoteros_ГельВсеТипыКожи_200","KSM_kosmoteros_себорегулятор_50","KSM_kosmoteros_крем15spf_50","KSM_kosmoteros_СывВитКомп_30","KSM_kosmoteros_КремИкра_25","KSM_kosmoteros_КремSL_25","KSM_kosmoteros_КремВитС_50","KSM_kosmoteros_КремСПФ30_50","KSM_kosmoteros_Ремодулятор_30","KSM_kosmoteros_кремIB_50","KSM_Kosmoteros_МаскаЭкспрессЛифтинг_50","KSM_Kosmoteros_МаскаМорКоллаген_50","KSM_Kosmoteros_ЛосьонБиоактиватор_200","KSM_Kosmoteros_ГельAnticouperose_50","KSM_Kosmoteros_КремМорКоллаген_50","GRT_HealthIs_МужскиеВитамины_120","GRT_HealthIs_Пробиотики_120","KSM_Kosmoteros_ПилингГоммаж_50","KSM_kosmoteros_ГельМаска_50","UNL_ЧистаяЛиния_ГифтПерсик_190","GRT_HealthIs_Кальций_120","KSM_kosmoteros_крембриллиант_50","GRT_HealthIs_КреатинМалина_300","GRT_Kottur_СкрабЛимонныйДесерт_350","GRT_Kottur_СкрабКокос_350","GRT_Kottur_КремДляВек_20","GRT_Kottur_КремБаттерКокос_300","GRT_Kottur_КремБаттерLostCherry_300","GRT_Kottur_МагниевоеМасло_200","GRT_HealthIs_Д3К2таблетки_180",
]

WAREHOUSE_DEFECTS = ["пришел другой дозатор", "нет этикетки", "нет дозатора",
                     "нет товара", "пришел разбитым", "перепутан штрихкод", "перепутан товар",
                     "брак", "проблема с этикеткой", "просрочка", "нет упаковки"]

DEFECT_CATEGORIES = {
    "пришел другой дозатор": "комплектация",
    "нет этикетки": "этикетка",
    "нет дозатора": "комплектация",
    "нет товара": "комплектация",
    "пришел разбитым": "перевозка",
    "перепутан штрихкод": "этикетка",
    "перепутан товар": "смена товара",
    "брак": "брак",
    "проблема с этикеткой": "этикетка",
    "нет упаковки": "упаковка",
    "просрочка": "просрочка"}

PRODUCTION_DEFECTS = ["нет даты производства ", "волос в банке", "пустая банка", "банка без защитной фольги",
                      "расплавленный вид", "недостающее количество капсул", "капсулы в масле", "капсулы в пятнах",
                      "черная крышка внутри банки", "неприятный запах от капсул", "пустые капсулы в банке ",
                      "просрочка", "вскрытая банка", "пришел без этикетки", "вскрыт пакет с селикагелем",
                      "жалоба на плесень ", ]

MARKETPLACES = ["вб", "озон", "ям"]


def init_google_sheets():
    try:
        private_key_id = os.environ.get("KEY_1")
        private_key = os.environ.get("KEY_2")

        if not private_key_id or not private_key:
            raise Exception("хуйня ебучая")

        
        service_account_data = {
            "type": "service_account",
            "project_id": "brakpoduction55",
            "private_key_id": private_key_id,
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": "brakgarantis55@brakpoduction55.iam.gserviceaccount.com",
            "client_id": "111941743629865868932",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/brakgarantis55%40brakpoduction55.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        creds = Credentials.from_service_account_info(
            service_account_data,
            scopes=SCOPES
        )

        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)

        logger.info("успешное подключение к Google Sheets")
        return spreadsheet

    except Exception as e:
        logger.error(f"ошибка подключения к Google Sheets: {e}")
        return None


def ensure_sheets_exist(spreadsheet):
    try:
        existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]

        if SHEET_NAMES['warehouse'] not in existing_sheets:
            warehouse_sheet = spreadsheet.add_worksheet(
                title=SHEET_NAMES['warehouse'],
                rows=1000,
                cols=10
            )
            warehouse_sheet.append_row([
                "Дата", "Автор", "Код продукта", "Маркетплейс",
                "Описание проблемы", "Характеристика проблемы", "Текст сообщения"
            ])
            logger.info(f"Создан лист: {SHEET_NAMES['warehouse']}")

        if SHEET_NAMES['production'] not in existing_sheets:
            production_sheet = spreadsheet.add_worksheet(
                title=SHEET_NAMES['production'],
                rows=1000,
                cols=10
            )
            production_sheet.append_row([
                "Дата", "Автор", "Код продукта", "Маркетплейс",
                "Описание проблемы", "Текст сообщения"
            ])
            logger.info(f"создан лист: {SHEET_NAMES['production']}")

        return True

    except Exception as e:
        logger.error(f"ошибка листов: {e}")
        return False


def write_to_google_sheets(data, sheet_type):
    try:
        with lock:
            spreadsheet = init_google_sheets()
            if not spreadsheet:
                return False

            ensure_sheets_exist(spreadsheet)

            sheet_name = SHEET_NAMES[sheet_type]
            worksheet = spreadsheet.worksheet(sheet_name)

            worksheet.append_row(data)

            logger.info(f"данные записаны в {sheet_name}")
            return True

    except Exception as e:
        logger.error(f"хуйня в Google Sheets: {e}")
        return False


def normalize(text):
    return re.sub(r'[\s_]+', '', text.lower())


def find_match(text, collection):
    text_norm = normalize(text)
    for item in collection:
        if normalize(item) in text_norm:
            return item
    return ""


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.args.get("token") != WEBHOOK_TOKEN:
        logger.warning("неверный токен")
        return jsonify({"error": "Forbidden"}), 403

    try:
        data = request.get_json()
        if not data:
            logger.error("Пустой запрос")
            return jsonify({"error": "No data provided"}), 400

        text = str(data.get("content", "")).strip().lower()
        author = data.get("user_id", "Неизвестно")

        time_str = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"обработка запроса от {author}: {text}")

        success = False

        if text.startswith("#склад"):
            product = find_match(text, PRODUCTS)
            defect = find_match(text, WAREHOUSE_DEFECTS)
            marketplace = find_match(text, MARKETPLACES)

            if not defect:
                success = write_to_google_sheets([
                    time_str,
                    author,
                    "",
                    marketplace if marketplace else "",
                    "",
                    "",
                    text
                ], "warehouse")
            else:
                success = write_to_google_sheets([
                    time_str,
                    author,
                    product,
                    marketplace if marketplace else "",
                    defect,
                    DEFECT_CATEGORIES.get(defect, ""),
                    text
                ], "warehouse")


        
        elif text.startswith("#производство"):
            product = find_match(text, PRODUCTS)
            defect = find_match(text, PRODUCTION_DEFECTS)
            marketplace = find_match(text, MARKETPLACES)

            if not defect:
                success = write_to_google_sheets([
                    time_str,
                    author,
                    "",
                    marketplace if marketplace else "",
                    "",
                    text
                ], "production")
            else:
                success = write_to_google_sheets([
                    time_str,
                    author,
                    product,
                    marketplace if marketplace else "",
                    defect,
                    text
                ], "production")

        else:
            return jsonify({"status": "ignored"}), 200
        if success:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "failed"}), 500

    except Exception as e:
        logger.exception(f"хуйня в Google Sheets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    try:
        spreadsheet = init_google_sheets()
        if spreadsheet:
            return jsonify({"status": "healthy", "sheets_connected": True})
        else:
            return jsonify({"status": "unhealthy", "sheets_connected": False}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    logger.info("зависимости")

    logger.info("сервер")

    spreadsheet = init_google_sheets()
    if spreadsheet:
        logger.info("все ок гугл щитс")
        ensure_sheets_exist(spreadsheet)
    else:
        logger.error("1")
        logger.error("2")
        logger.error("3")
        logger.error("4")

    logger.info(f"Сервер запущен на {BIND_HOST}:{PORT}")
    logger.info(f"Health check: http://{BIND_HOST}:{PORT}/health")

    app.run(host=BIND_HOST, port=PORT, debug=True)












