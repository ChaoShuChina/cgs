import codecs
import os
import sys

from config import CONFIG
from app.data import data_manager
from app.utils import db_utils

try:
    import matplotlib.pyplot as plt
except ImportError, e:
    print "ImportError: No module named matplotlib.pyplot"


def translate_mapgis(source_dir, target_dir, layers, map_id):
    slib = dict()
    for fname in os.listdir(source_dir):
        if '.txt' in fname:
            result = create_layerstyle(source_dir, fname, map_id)
            layer = result["layer"]
            symbol_lid = result["symbol_lib"]
            slib.update(symbol_lid)
            lyr = fname.split(".")[0]
            for obj in layers:
                if obj["name"] == lyr:
                    alter_table(str(obj["id"]), layer)
                    break
            create_mss(target_dir, layer)
        upload_sym(slib, map_id)
        if '.wat' in fname:
            lyr = fname.split(".")[0]
            for obj in layers:
                if obj["name"] == lyr:
                    result = create_notestyle(source_dir, obj, fname, map_id)
                    layer = result["layer"]
                    break
            create_notemss(target_dir, layer)


def savemath(formula, col, key, map_id):
    mname = "note" + key + ".png"
    save_path = os.path.join(CONFIG["map"]["map_dir"], str(map_id), "images")
    fig = plt.figure()
    text = fig.text(0, 0, formula, color=col, fontsize=20, style='italic')
    dpi = 300
    fig.savefig(os.path.join(save_path, mname), dpi=dpi, transparet=True)

    bbox = text.get_window_extent()
    width, height = bbox.size / float(dpi) + 0.03

    fig.set_size_inches((width, height))

    dy = (bbox.ymin / float(dpi)) / height
    text.set_position((0, -dy))

    fig.savefig(os.path.join(save_path, mname), facecolor='none', dpi=dpi, transparet=True)


def create_notestyle(source_dir, obj, fname, map_id):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    f = codecs.open(os.path.join(source_dir, fname), 'r', encoding="gb2312")
    app_id = obj["id"]
    table_name = data_manager.get_geology_tablename(app_id)
    statement = "alter table " + str(table_name) + " add column style_id int "
    db_utils.execute_geo_ddl(statement)
    n = -2
    layer = {}
    result = {}
    stylelist = []
    res_set = {}
    num_set = {}
    res = {}
    slib = {}
    sym_set = {}
    res_setd = {}
    lyr = fname.split(".")
    layername = lyr[0]
    symbol_lib = {}
    layer["name"] = str(layername)
    for line in f.readlines():
        temp = line.split(",")
        n += 1
        try:
            if not temp[4].find('"'):
                note = temp[4].encode('utf-8')[1:-1]
                note_id = temp[2].encode('utf-8')
                note_fid = n
                if note.isdigit():  # 数字符号的转换
                    num_color = temp[13]
                    if num_color == "6":
                        num_id = "r1000" + note
                    else:
                        num_id = "b1000" + note
                    if num_id not in num_set:
                        num_set[num_id] = {}
                    res = num_set[num_id]
                    if note not in res:
                        res[note] = []
                    res[note].append(note_fid)
                    marker_file = "url(images/note" + num_id + ".png)"
                    marker_width = temp[5]
                    marker_transform = str(float(temp[7]))
                    s = {}
                    s["marker-file"] = marker_file
                    s["marker-width"] = str(float(marker_width) * 5)
                    s["marker-allow-overlap"] = "true"
                    existed = False
                    for item in stylelist:
                        if item["style"] == s:
                            item["id"].append(note_fid)
                            existed = True
                    if existed is False:
                        item = {}
                        item["id"] = []
                        item["id"].append(note_fid)
                        item["style"] = s
                        stylelist.append(item)

                else:  # 注释符号的转换
                    note_id = "2000" + note_id
                    if note_id not in res_set:
                        res_set[note_id] = {}
                    res = res_set[note_id]
                    if note not in res:
                        res[note] = []
                    res[note].append(note_fid)
            else:  # 符号标注的转换
                symbol_id = temp[4].encode('utf-8')
                note_id = "3000" + symbol_id
                symbol_fid = n
                if symbol_id not in sym_set:
                    sym_set[symbol_id] = {}
                sym = sym_set[symbol_id]
                if note_id not in sym:
                    sym[note_id] = []
                sym[note_id].append(symbol_fid)
                marker_file = "url(images/svg" + symbol_id + ".svg)"
                marker_width = temp[5]
                marker_height = temp[6]
                if symbol_id == '1429':
                    marker_transform = str(180 - float(temp[7]))
                else:
                    marker_transform = str(360 - float(temp[7]))
                if temp[9] == "6":
                    marker_line_color = "rgb(255,0,0)"
                if temp[9] == "1":
                    marker_line_color = "rgb(0,0,0)"
                symbol_lib[symbol_id] = ""
                s = {}
                s["marker-file"] = marker_file
                #                s["marker-width"] = str(float(marker_width) * 5)
                s["marker-height"] = str(float(marker_height) * 1.5)
                s["marker-transform"] = "rotate(" + marker_transform + ",0,0)"
                s["marker-line-color"] = marker_line_color
                s["marker-allow-overlap"] = "true"
                existed = False
                for item in stylelist:
                    if item["style"] == s:
                        item["id"].append(symbol_fid)
                        existed = True
                if existed is False:
                    item = {}
                    item["id"] = []
                    item["id"].append(symbol_fid)
                    item["style"] = s
                    stylelist.append(item)
        except IndexError:
            pass
    for key in sym_set.keys():
        slib[key] = ''
        symbol_id = key
        note_id = str(sym_set[key].keys())[2:-2]
        fid = str(sym_set[key][note_id])[1:-1]
        sql = "UPDATE " + table_name + " set id = " + str(
            note_id) + ",dsn ='" + symbol_id + "' where ogc_fid in (" + fid + ") "
        db_utils.execute_geo_ddl(sql)
    upload_sym(slib, map_id)
    layer["stylelist"] = stylelist
    result["layer"] = layer
    # 注释符号整合解析
    for key in res_set.keys():
        temp = res_set[key]
        tempd = {}
        noted = ''
        resd = sorted(temp.iteritems(), key=lambda a: a[1][0], reverse=False)
        for i in range(len(resd)):
            noted += resd[i][0]
            numd = resd[0][1]
        math = "$" + noted.replace('#+', '^').replace('#-', '_').replace('#=', '') + "$"
        res_setd[key] = {}
        tempd = res_setd[key]
        tempd[math] = numd
    color = "black"
    for key in num_set.keys():
        num_id = key
        nid = num_id[1:]
        formula = ''.join(num_set[key].keys())
        fid = str(num_set[key][formula])[1:-1]
        sql = "UPDATE " + table_name + " set id = " + str(
            nid) + ",dsn ='" + formula + "' where ogc_fid in (" + fid + ") "
        db_utils.execute_geo_ddl(sql)
        if "r" in num_id:
            color = 'red'
        else:
            color = 'black'
        savemath(formula, color, key, map_id)
    for key in res_setd.keys():
        s = {}
        nid = key
        formula = ''.join(res_setd[key].keys())
        fid = str(res_setd[key][formula])[1:-1]
        sql = "UPDATE " + table_name + " set id = " + str(
            nid) + ",dsn ='" + formula + "' where ogc_fid in (" + fid + ") "
        db_utils.execute_geo_ddl(sql)
        savemath(formula, color, key, map_id)
        note_file = "url(images/note" + key + ".png)"
        s["marker-file"] = note_file
        s["marker-width"] = 15
        s["marker-line-width"] = 10
        s["marker-allow-overlap"] = "true"
        existed = False
        for item in stylelist:
            if item["style"] == s:
                item["id"].append(nid)
                existed = True
        if existed is False:
            item = {}
            item["id"] = []
            item["id"].append(fid)
            item["style"] = s
            stylelist.append(item)
    cnt = 1
    for item in stylelist:
        item["styleid"] = cnt
        style_id = cnt
        ids = item["id"]
        idstr = reduce("{0},{1}".format, ids)
        SQL = "update " + table_name + " set style_id = " + str(style_id) + " where ogc_fid in (" + str(idstr) + ") "
        db_utils.execute_geo_ddl(SQL)
        cnt += 1
    layer["stylelist"] = stylelist
    result["layer"] = layer
    return result


# 解析样式对应文件txt
def create_layerstyle(source_dir, fname, map_id):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    layer = {}
    result = {}
    stylelist = []
    symbol_lib = {}
    lyr = fname.split(".")
    layertype = lyr[1]
    layername = lyr[0]
    layer["name"] = layername
    f = open(os.path.join(source_dir, fname), 'r')
    if layertype == 'WP':
        for line in f.readlines():
            temp = line.split(",")
            fid = temp[0]
            s = {}
            color = temp[1].split("|")
            rgb = "rgb(" + color[1] + "," + color[2] + "," + color[3] + ")"
            s["polygon-fill"] = rgb
            existed = False
            for item in stylelist:
                if item["style"] == s:
                    item["id"].append(fid)
                    existed = True
            if existed is False:
                item = {}
                item["id"] = []
                item["id"].append(fid)
                item["style"] = s
                stylelist.append(item)
    elif layertype == 'WT':
        for line in f.readlines():
            temp = line.split(",")
            fid = temp[0]
            symbol_id = temp[2]
            marker_file = "url(images/svg" + symbol_id + ".svg)"
            marker_width = temp[3]
            marker_transform = str(180 - float(temp[5]))
            symbol_lib[symbol_id] = ""
            s = {}
            s["marker-file"] = marker_file
            s["marker-width"] = str(float(marker_width) * 3)
            #            s["marker-height"] = str(float(marker_height) * 2)
            s["marker-transform"] = "rotate(" + marker_transform + ",0,0)"
            if temp[7].split("|")[0] != "0":
                color = temp[7].split("|")
            else:
                color = temp[10].split("|")
            rgb = "rgb(" + color[1] + "," + color[2] + "," + color[3] + ")"
            s["marker-line-color"] = rgb
            existed = False
            for item in stylelist:
                if item["style"] == s:
                    item["id"].append(fid)
                    existed = True
            if existed is False:
                item = {}
                item["id"] = []
                item["id"].append(fid)
                item["style"] = s
                stylelist.append(item)
    elif layertype == 'WL':
        for line in f.readlines():
            temp = line.split(",")
            fid = temp[0]
            s = {}
            color = temp[4].split("|")
            rgb = "rgb(" + color[1] + "," + color[2] + "," + color[3] + ")"
            width = temp[5] + "mm "
            s["line-color"] = rgb
            s["line-width"] = width
            existed = False
            for item in stylelist:
                if item["style"] == s:
                    item["id"].append(fid)
                    existed = True
            if existed is False:
                item = {}
                item["id"] = []
                item["id"].append(fid)
                item["style"] = s
                stylelist.append(item)
    cnt = 1
    for item in stylelist:
        item["styleid"] = cnt
        cnt += 1
    layer["stylelist"] = stylelist
    result["layer"] = layer
    result["symbol_lib"] = symbol_lib
    return result


def upload_sym(slib, map_id):
    source_dir = CONFIG["symbols"]["path"] + "20wgeology"
    dest_dir = os.path.join(CONFIG["map"]["map_dir"], str(map_id), "images")
    for key in slib:
        sym_name = "svg" + key + ".svg"
        shutil.copyfile(os.path.join(source_dir, sym_name), os.path.join(dest_dir, sym_name))


def alter_table(app_id, layer):
    table_name = get_geology_tablename(app_id)
    statement = "alter table " + str(table_name) + " add column style_id int "
    db_utils.execute_geo_ddl(statement)
    for temp in layer["stylelist"]:
        style_id = temp["styleid"]
        ids = temp["id"]
        idstr = reduce("{0},{1}".format, ids)
        SQL = "update " + table_name + " set style_id = " + str(style_id) + " where ogc_fid in (" + str(idstr) + ") "
        db_utils.execute_geo_ddl(SQL)


def create_mss(target_dir, layer):
    mssfile = open(target_dir, 'a')
    layer_mss = "Map{\n buffer-size:1024;\n}\n#" + layer["name"] + "{ \n"
    for temp in layer["stylelist"]:
        style = temp["style"]
        layer_mss += "[style_id = " + str(temp["styleid"]) + "] {\n"
        for key in style.keys():
            layer_mss += "  " + str(key) + ":" + style[key] + ";\n"
        layer_mss += "}\n"
    layer_mss += "}"
    mssfile.writelines(layer_mss)


def create_notemss(target_dir, layer):
    mssfile = open(target_dir, 'a')
    layer_mss = "Map{\n buffer-size:1024;\n}\n#" + layer["name"] + "{ \n"
    for temp in layer["stylelist"]:
        style = temp["style"]
        layer_mss += "[style_id = " + str(temp["styleid"]) + "] {\n"
        for key in style.keys():
            layer_mss += "  " + str(key) + ":" + str(style[key]) + ";\n"
        layer_mss += "}\n"
    layer_mss += "}"
    mssfile.writelines(layer_mss)
