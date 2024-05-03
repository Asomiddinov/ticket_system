import json
import pytz
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, send_file, abort, jsonify
from .__init__ import create_app, db
from .models import QRCodeData, Mine, User, Note, Reg, Filters, Tasks, Orgdata, Production, Exhibition, Seat
import secrets
import qrcode
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
# from pywinauto.application import Application
app = create_app()
# notification section
socketio = SocketIO(app)


@socketio.on('assign user')
def assign_user(message):
    emit('notification', {
         'data': 'User ' + message['user'] + ' has been assigned a new post'}, broadcast=True)


# end of notification section
# Time section
now_utc = datetime.now(pytz.utc)
tz = pytz.timezone('Asia/Tashkent')
now_uz = now_utc.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
#
# Payment section:
# api_token = 'D749B114FBCC4FE8B42ACA2D0FE75064'
# secret_code = 'FDF026292FEC448E9341A603E42CD8A2'
# headers = {
#     'Authorization': f'{api_token}:{secret_code}',
#     'accept': 'application/json',
#     'content-type': 'application/*+json'
# }
###############


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    return render_template("index.html", user=current_user)


############################## El Merosi #######################################
@app.route("/exhibition", methods=["GET", "POST"])
def exhibition():
    if request.method == "POST":
        new_ticket = Exhibition(
            exh_datetime=request.form["exh_datetime"],
            exh_name=request.form["exh_name"]
        )
        seats = Seat.query.all()
        for seat in seats:
            new_ticket.seats.append(seat)
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for("tickets"))
    return render_template("exhibition.html", user=current_user)


@app.route("/seat", methods=["GET", "POST"])
def seat():
    if request.method == "POST":
        new_seat = Seat(
            seat_number=request.form["seat_number"],
            price=request.form["price"]
        )
        db.session.add(new_seat)
        db.session.commit()
        return redirect(url_for("seat"))
    return render_template("seat.html", user=current_user, seats=Seat.query.all())


@app.route("/tickets")
def tickets():
    return render_template("tickets.html", user=current_user, exh=Exhibition.query.all())


@app.route("/ticket/<int:id>")
def ticket(id):
    return render_template("ticket.html", user=current_user, ticket=Exhibition.query.get(id), seats=Seat.query.all())

# exhibition.seats.append(seat)
# db.session.commit()
# flash('The seat has been successfully booked!', 'success')


@app.route("/book_seats/<exh_name>/<int:seat_id>", methods=["POST", "GET"])
def book_seats(exh_name, seat_id):
    seat = Seat.query.get(seat_id)
    exhibition = Exhibition.query.filter_by(exh_name=exh_name).first()
    if seat:
        client_name = request.args.get('client_name')
        client_phone = request.args.get('client_phone')
        api_token = 'D749B114FBCC4FE8B42ACA2D0FE75064'
        secret_code = 'FDF026292FEC448E9341A603E42CD8A2'
        headers = {
            'Authorization': f'{api_token}:{secret_code}',
            'accept': 'application/json',
            'content-type': 'application/*+json'
        }
        data = {
            "hooks": {
                "webhookGateway": f"https://basomiddinov.pythonanywhere.com/ticket/{seat_id}",
                "successRedirectGateway": f"https://basomiddinov.pythonanywhere.com/ticket_success/{client_name}_%_{client_phone}_{exh_name}%_%{seat_id}",
                "errorRedirectGateway": "https://basomiddinov.pythonanywhere.com/ticket/"
            },
            "source": "Card",
            "amount": 1,
            "currency": "UZS",
            "metadata": {
                "order": {
                        "orderId": f"{client_name}{client_phone}{exh_name}{seat_id}",
                        "uzRegulatoryOrderDetails": {
                            "latitude": 43.231231,
                            "longitude": 232.2131231,
                            "taxiVehicleNumber": "...",
                            "taxiTin": "...",
                            "taxiPinfl": "..."
                        },
                    "orderItems": [
                            {
                                "uzRegulatoryOrderItem": {
                                    "commissionInfoPinfl": "31711953970057",
                                    "commissionInfoTin": "..."
                                },
                                "productLink": f"https://basomiddinov.pythonanywhere.com/ticket/{seat_id}",
                                "productImage": "https://basomiddinov.pythonanywhere.com/tickets",
                                "productName": "ticket_from_babai.io",
                                "productCode": "11201001001000000",
                                "productBarCode": "Raqamli axborot texnologiyalari sohasidagi xizmatlar",
                                "productLabel": "...",
                                "packageCode": "112",
                                "productQuantity": 1,
                                "price": seat.price,
                                "sumPrice": seat.price,
                                "vat": 0,
                                "vatPercent": 0,
                                "discount": 0,
                                "additionalDiscount": 0
                            }
                        ],
                    "billingAddress": {
                            "phoneNumber": f"{client_phone}"
                        }
                },
                "extraAttributes": [
                    {
                        "key": "RECEIPT_TYPE",
                        "value": "Sale",
                        "description": "OFD Receipt type"
                    }
                ]
            }
        }
        data_json = json.dumps(data)
        url = 'https://payze.io/v2/api/payment'
        proxies = {
            'http': 'http://proxy.server:3128',
            'https': 'https://proxy.server:3128',
        }
        response = requests.put(url, headers=headers,
                                data=data_json, proxies=proxies)
        return render_template("booked_ticket.html", user=current_user, response=response)
    else:
        # f"https://basomiddinov.pythonanywhere.com/ticket/{exh_name}%_%{seat_id}"
        # f"https://basomiddinov.pythonanywhere.com/ticket/{exh_name}%_%{seat_id}"
        # f"https://basomiddinov.pythonanywhere.com/ticket_success/{client_name}_%_{client_phone}_{exh_name}%_%{seat_id}
        flash('This seat row is already full!', 'error')
    return redirect(url_for("ticket", id=exhibition.id))


@app.route("/ticket_success", methods=["GET", "POST"])
def ticket_success(exh_name, seat_id):
    # http://basomiddinov.pythonanywhere.com/ticket_success/{client_name}_%_{client_phone}_{exh_name}%_%{seat_id}
    exhibition_suc = Exhibition.query.filter_by(exh_name=exh_name).first()
    return render_template("ticket_success.html", exhibition_suc=exhibition_suc, user=current_user)


data = {
    "hooks": {
        "webhookGateway": "http://basomiddinov.pythonanywhere.com/ticket/1",
        "successRedirectGateway": "http://basomiddinov.pythonanywhere.com/ticket_success",
        "errorRedirectGateway": "http://basomiddinov.pythonanywhere.com/ticket/"
    },
    "source": "Card",
    "amount": 100,
    "currency": "UZS",
    "metadata": {
        "order": {
            "orderId": "1",
            "uzRegulatoryOrderDetails": {
              "latitude": 43.231231,
              "longitude": 232.2131231,
              "taxiVehicleNumber": "...",
              "taxiTin": "...",
              "taxiPinfl": "..."
            },
            "orderItems": [
                {
                    "uzRegulatoryOrderItem": {
                        "commissionInfoPinfl": "31711953970057",
                        "commissionInfoTin": "..."
                    },
                    "productLink": "http://basomiddinov.pythonanywhere.com/ticket/1?",
                    "productImage": "http://basomiddinov.pythonanywhere.com/ticket/1?",
                    "productName": "ticket_1",
                    "productCode": "11201001001000000",
                    "productBarCode": "Raqamli axborot texnologiyalari sohasidagi xizmatlar",
                    "productLabel": "...",
                    "packageCode": "112",
                    "productQuantity": 1,
                    "price": 100,
                    "sumPrice": 100,
                    "vat": 0,
                    "vatPercent": 0,
                    "discount": 0,
                    "additionalDiscount": 0
                }
            ],
            "billingAddress": {
                "phoneNumber": "+998939956232"
            }
        },
        "extraAttributes": [
            {
                "key": "RECEIPT_TYPE",
                "value": "Sale",
                "description": "OFD Receipt type"
            }
        ]
    }
}
data_json = json.dumps(data)
url = 'https://payze.io/v2/api/payment'
# response = requests.put(url, headers=headers, data=data_json)
# print(response.status_code)
# print(response.json())
################################################################################

# @app.route("/notif")
# def notif():
#     toast = notification.notify(
#         title='Test from Babai',
#         message='Go to Babai to see your tasks',
#         app_name='Windows app',
#         app_icon='Babai/static/images/babai.png')
#     return "Notification SENT"
subscriptions = []


@app.route('/subscribe', methods=['POST'])
def subscribe():
    subscription = request.get_json()
    subscriptions.append(subscription)
    return f"Subscription added! {subscriptions}"


# @app.route('/notify')
# def notify():
#     for subscription in subscriptions:
#         try:
#             webpush(
#                 subscription_info=subscription,
#                 data="Go to Babai to see your tasks",
#                 # Replace with the path to your private key file
#                 vapid_private_key="private_key.txt",
#                 # Replace with your email
#                 vapid_claims={"sub": "mailto:your-email@example.com"}
#             )
#         except WebPushException as ex:
#             print("I'm sorry, but I wasn't able to send the notification.", repr(ex))
#     return "Notifications sent!"


@app.route("/generator/", methods=["GET", "POST"])
@app.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    form = QRCodeData()
    if request.method == "POST":
        if form.validate_on_submit():
            dat = form.dat.data
            image_name = f"{secrets.token_hex(10)}.png"
            qrcode_location = f"{app.config['UPLOAD_PATH']}/{image_name}"
            try:
                my_qrcode = qrcode.make(
                    str(dat)).save(qrcode_location)
            except Exception as e:
                print(e)
            return render_template("generated.html", title="Generated QRCode", image=image_name, user=current_user)
    else:
        return render_template("generator.html", title="Babai QRCode", form=form, user=current_user)


@app.route("/action/", methods=["GET", "POST"])
@app.route("/action", methods=["GET", "POST"])
@login_required
def acted():
    form = Mine()
    file = request.files.get("files")
    datafile = pd.read_excel(file, header=None) if file else None
    if request.method == "POST":
        if datafile is None:
            reg = Reg(client=request.form.get("client"), address=request.form.get("address"), driver=request.form.get("driver"), con_note=request.form.get("con_note"),
                      paid=request.form.get("paid") or 0, date=request.form.get("date"), pre_width1=request.form.get("pre_width1"), pre_width2=request.form.get("pre_width2"),
                      pre_width3=request.form.get("pre_width3"), pre_width4=request.form.get("pre_width4"), pre_width5=request.form.get("pre_width5"),
                      mark=request.form.get("mark"), quantity=request.form.get("quantity"), price=request.form.get('price'), currency=request.form.get("currency"),
                      user_fullname=request.form.get("user_fullname"), client_id=request.form.get("client_id"), quantity_tray=request.form.get("quantity_tray"),
                      s_rep=request.form.get("s_rep"), price_rm=request.form.get("price_rm"), price_tray=request.form.get("price_tray"),
                      price_pre1=request.form.get("price_pre1"), price_pre2=request.form.get("price_pre2"), price_pre3=request.form.get("price_pre3"), price_pre4=request.form.get("price_pre4"), price_pre5=request.form.get("price_pre5"),
                      price_fbs06=request.form.get("price_fbs06"), price_fbs08=request.form.get("price_fbs08"), price_fbs09=request.form.get("price_fbs09"), price_fbs12=request.form.get("price_fbs12"), price_fbs24=request.form.get("price_fbs24"),
                      quantity_fbs1=request.form.get("quantity_fbs1"), quantity_fbs2=request.form.get("quantity_fbs2"),
                      quantity_fbs3=request.form.get("quantity_fbs3"), quantity_fbs4=request.form.get("quantity_fbs4"), quantity_fbs5=request.form.get("quantity_fbs5"),
                      precast1=request.form.get("precast1"), precast2=request.form.get("precast2"), precast3=request.form.get("precast3"), precast4=request.form.get("precast4"), precast5=request.form.get("precast5"),
                      length1=request.form.get("length1"), length2=request.form.get("length2"), length3=request.form.get("length3"), length4=request.form.get("length4"), length5=request.form.get("length5"),
                      type1=request.form.get("type1"), type2=request.form.get("type2"), type3=request.form.get("type3"), type4=request.form.get("type4"), type5=request.form.get("type5"))
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for("info_id", id=reg.id))
        if datafile is not None:
            reg = Reg(
                client_id=datafile.iloc[1, 6], client="_____", address=datafile.iloc[22, 6], quantity=datafile.iloc[10, 6], mark=datafile.iloc[2, 6],
                con_note=request.form.get("con_note"), price=request.form.get("price"), price_rm=request.form.get("price_rm"), price_tray=request.form.get("price_tray"),
                price_pre1=request.form.get("price_pre1"), price_pre2=request.form.get("price_pre2"), price_pre3=request.form.get("price_pre3"), price_pre4=request.form.get("price_pre4"),
                price_pre5=request.form.get("price_pre5"),
                price_fbs06=request.form.get("price_fbs06"), price_fbs08=request.form.get("price_fbs08"), price_fbs09=request.form.get("price_fbs09"),
                price_fbs12=request.form.get("price_fbs12"), price_fbs24=request.form.get("price_fbs24"), paid=0, currency=request.form.get("currency"),
                user_fullname=request.form.get("user_fullname"), driver=datafile.iloc[22, 6], date=datafile.iloc[4, 6], pre_width1=request.form.get("pre_width1"), pre_width2=request.form.get("pre_width2"),
                pre_width3=request.form.get("pre_width3"), pre_width4=request.form.get("pre_width4"), pre_width5=request.form.get("pre_width5"), quantity_tray=request.form.get("quantity_tray"),
                s_rep=request.form.get("s_rep"), precast1=request.form.get("precast1"), precast2=request.form.get("precast2"), precast3=request.form.get("precast3"), precast4=request.form.get("precast4"), precast5=request.form.get("precast5"),
                length1=request.form.get("length1"), length2=request.form.get("length2"), length3=request.form.get("length3"), length4=request.form.get("length4"), length5=request.form.get("length5"),
                type1=request.form.get("type1"), type2=request.form.get("type2"), type3=request.form.get("type3"), type4=request.form.get("type4"), type5=request.form.get("type5"),
                quantity_fbs1=request.form.get("quantity_fbs1"), quantity_fbs2=request.form.get("quantity_fbs2"), quantity_fbs3=request.form.get("quantity_fbs3"), quantity_fbs4=request.form.get("quantity_fbs4"), quantity_fbs5=request.form.get("quantity_fbs5"),
            )
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for("info_id", id=reg.id))
    else:
        return render_template("action.html", user=current_user, form=form)


@app.route("/info/", methods=["GET", "POST"])
@app.route("/info", methods=["GET", "POST"])
def info():
    form = Mine()
    reg = Reg.query.filter_by(id=Reg.id).all()
    if form.validate_on_submit:
        total_price = 0
        total_prices = []
        for row in reg:
            data = {'quantity': [row.quantity, row.quantity_tray, row.quantity_fbs1, row.quantity_fbs2, row.quantity_fbs3, row.quantity_fbs4, row.quantity_fbs5, row.length1, row.length2, row.length3, row.length4, row.length5],
                    'price': [row.price_rm, row.price_tray, row.price_fbs06, row.price_fbs08, row.price_fbs09, row.price_fbs12, row.price_fbs24, row.price_pre1, row.price_pre2, row.price_pre3, row.price_pre4, row.price_pre5],
                    'precast': [1, 1, 1, 1, 1, 1, 1, row.precast1, row.precast2, row.precast3, row.precast4, row.precast5]}
            df = pd.DataFrame(data)
            # df['quantity'] = df['quantity'].apply(lambda x: float(x) if x != '' else 0)
            df['quantity'] = df['quantity'].apply(
                lambda x: float(x) if x not in ('', None) else 0)
            df['price'] = df['price'].apply(
                lambda x: float(x) if x not in ('', None) else 0)
            df['precast'] = df['precast'].apply(
                lambda x: float(x) if x not in ('', None) else 1)
            total_price = (df['quantity']*df['price']*df['precast']).sum()
            total_prices.append(total_price)
        sum_total_prices = sum(total_prices)
        balance_paid = 0
        for i in reg:
            balance_paid = balance_paid + i.paid
        return render_template("info.html", form=form, reg=reg, user=current_user, balance_paid=balance_paid,
                               total_price=total_price, total_prices=total_prices, sum_total_prices=sum_total_prices)


@app.route("/info/<client>/<client_id>/")
@app.route("/info/<client>/<client_id>")
@login_required
def info_client(client, client_id):
    form = Mine()
    if client:
        e = Reg.query.filter_by(client=client, client_id=client_id).all()
        balance_paid = 0
        for i in e:
            balance_paid = balance_paid + i.paid
        return render_template("info_client.html", user=current_user, e=e, form=form, balance_paid=balance_paid)
    else:
        flash("No that client_id!", "error")
        return render_template("info.html", user=current_user, form=form)


@app.route("/info/<int:id>/", methods=["GET", "POST"])
@app.route("/info/<int:id>", methods=["GET", "POST"])
@login_required
def info_id(id):
    form = Mine()
    if form.validate_on_submit:
        exact = Reg.query.get_or_404(id)
        return render_template("info_id.html", form=form, exact=exact, user=current_user)


@app.route("/update/<int:id>/", methods=["GET", "POST"])
@app.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    form = Mine()
    updater = Reg.query.get_or_404(id)
    if request.method == "POST":
        updater.con_note = form.con_note.data
        updater.client_id = form.client_id.data
        updater.client = form.client.data
        updater.address = form.address.data
        updater.mark = form.mark.data
        updater.quantity = form.quantity.data
        updater.quantity_tray = form.quantity_tray.data
        updater.s_rep = form.s_rep.data
        updater.quantity_fbs1 = form.quantity_fbs1.data
        updater.quantity_fbs2 = form.quantity_fbs2.data
        updater.quantity_fbs3 = form.quantity_fbs3.data
        updater.quantity_fbs4 = form.quantity_fbs4.data
        updater.quantity_fbs5 = form.quantity_fbs5.data
        updater.precast1 = form.precast1.data
        updater.precast2 = form.precast2.data
        updater.precast3 = form.precast3.data
        updater.precast4 = form.precast4.data
        updater.precast5 = form.precast5.data
        updater.length1 = form.length1.data
        updater.length2 = form.length2.data
        updater.length3 = form.length3.data
        updater.length4 = form.length4.data
        updater.length5 = form.precast5.data
        updater.pre_width1 = form.pre_width1.data
        updater.pre_width2 = form.pre_width2.data
        updater.pre_width3 = form.pre_width3.data
        updater.pre_width3 = form.pre_width4.data
        updater.pre_width5 = form.pre_width5.data
        updater.price = form.price.data
        updater.currency = form.currency.data
        updater.paid = form.paid.data
        updater.driver = form.driver.data
        updater.date = form.date.data
        db.session.add(updater)
        db.session.commit()
        flash("Client data updated successfully!", "success")
        return redirect(url_for("info_id", id=updater.id))
    form.con_note.data = updater.con_note
    form.client_id.data = updater.client_id
    form.client.data = updater.client
    form.address.data = updater.address
    form.mark.data = updater.mark
    form.quantity.data = updater.quantity
    form.quantity_tray.data = updater.quantity_tray
    form.s_rep.data = updater.s_rep
    form.quantity_fbs1.data = updater.quantity_fbs1
    form.quantity_fbs2.data = updater.quantity_fbs2
    form.quantity_fbs3.data = updater.quantity_fbs3
    form.quantity_fbs4.data = updater.quantity_fbs4
    form.quantity_fbs5.data = updater.quantity_fbs5
    form.precast1.data = updater.precast1
    form.precast2.data = updater.precast2
    form.precast3.data = updater.precast3
    form.precast4.data = updater.precast4
    form.precast5.data = updater.precast5
    form.length1.data = updater.length1
    form.length2.data = updater.length2
    form.length3.data = updater.length3
    form.length4.data = updater.length4
    form.length5.data = updater.length5
    form.pre_width1.data = updater.pre_width1
    form.pre_width1.data = updater.pre_width2
    form.pre_width1.data = updater.pre_width3
    form.pre_width1.data = updater.pre_width4
    form.pre_width1.data = updater.pre_width5
    form.price.data = updater.price
    form.currency.data = updater.currency
    form.paid.data = updater.paid
    form.driver.data = updater.driver
    form.date.data = updater.date
    return render_template("update.html", updater=updater, form=form, user=current_user)


@app.route("/filter_date/", methods=["GET", "POST"])
@app.route("/filter_date", methods=["GET", "POST"])
@login_required
def filter_date():
    form = Filters()
    balance_paid = 0
    if request.method == "POST":
        stdate = form.startdate.data
        enddate = form.enddate.data
        filter_date = Reg.query.filter(Reg.date.between(stdate, enddate)).all()
        for i in filter_date:
            balance_paid += i.paid
        # Create a Pandas DataFrame from the filtered data
        df = pd.DataFrame([(i.client_id, i.date, i.client, i.s_rep, i.mark, i.quantity, i.paid) for i in filter_date],
                          columns=['Client ID', 'Date', 'Client', 'Sales rep', 'RM', 'RM quantity', 'Paid'])
        # , i.quantity_tray, i.quantity_fbs1, i.quantity_fbs2, i.quantity_fbs3, i.quantity_fbs4, i.quantity_fbs5, i.precast1, i.precast2, i.precast3, i.precast4, i.precast5
        # , 'Tray', 'FBS1', 'FBS2', 'FBS3', 'FBS4', 'FBS5', 'Precast1', 'Precast2', 'Precast3', 'Precast4', 'Precast5','Paid', 'Price', 'Balance'
        # Blank for new table:
        blank = pd.Series(['', '', '', '', '', '', ''], index=df.columns)
        df = df.append(blank, ignore_index=True)
        # New tables:
        tray_row = pd.Series(['Client ID', 'Date', 'Client',
                             'Sales rep', 'Tray', 'Paid', ''], index=df.columns)
        df = df.append(tray_row, ignore_index=True)
        # Create a file path for the Excel file
        filename = os.path.join(
            app.static_folder, 'filtered_data', 'filtered_data.xlsx')
        # Export the DataFrame to an Excel file using a context manager
        with pd.ExcelWriter(filename) as writer:
            df.to_excel(writer, index=False, sheet_name="Filtered Data")
        # Render the template with a link to download the Excel file
        return render_template("filter_date.html", filter_date=filter_date, form=form, user=current_user, balance_paid=balance_paid)
    return render_template("filter_date.html", form=form, user=current_user)
    # Multiple tables:
    # tray_row_title = ['Client ID', 'Date', 'Client', 'Sales rep', 'Tray', '']
    # df.loc[len(df)] = tray_row_title
    # all_tray = [i.quantity_tray for i in filter_date] # Assuming the filtered data is 'quantity_tray'
    # # df.loc[:, 'Tray'] = all_tray
    # df['Tray'] = all_tray[:len(df)]


@app.route("/download_filtered_data")
@login_required
def download_filtered_data():
    # Create a file path for the Excel file
    filename = os.path.join(app.root_path, 'static',
                            'filtered_data', 'filtered_data.xlsx')
    # Send the Excel file as a download to the user's desktop
    return send_file(filename, as_attachment=True, attachment_filename='filtered_data.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if request.method == "POST":
        note = request.form.get("note")
        if len(note) < 1:
            flash("At least 1 characters", category="error")
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash("Note added!", category="success")
    return render_template("notes.html", user=current_user)


@app.route("/orders", methods=["GET", "POST"])
@login_required
def orders():
    form = Mine()
    if request.method == "POST":
        return redirect(url_for("index"))
    return render_template("orders.html", form=form, user=current_user)


@app.route("/production", methods=["GET", "POST"])
def production():
    form = Mine()
    production = Production(
        mark=request.form.get("mark"), quantity=request.form.get("quantity"),
        quantity_tray=request.form.get("quantity_tray"),
        quantity_fbs1=request.form.get("quantity_fbs1"), quantity_fbs2=request.form.get("quantity_fbs2"), quantity_fbs3=request.form.get("quantity_fbs3"),
        quantity_fbs4=request.form.get("quantity_fbs4"), quantity_fbs5=request.form.get("quantity_fbs5"),
        precast1=request.form.get("precast1"), precast2=request.form.get("precast2"), precast3=request.form.get("precast3"),
        precast4=request.form.get("precast4"), precast5=request.form.get("precast5"),
        length1=request.form.get("length1"), length2=request.form.get("length1"), length3=request.form.get("length3"),
        length4=request.form.get("length4"), length5=request.form.get("length5"),
        pre_width1=request.form.get("pre_width1"), pre_width2=request.form.get("pre_width2"), pre_width3=request.form.get("pre_width3"),
        pre_width4=request.form.get("pre_width4"), pre_width5=request.form.get("pre_width5")
    )
    if request.method == "POST":
        db.session.add(production)
        db.session.commit()
        flash("It's produced", category="success")
        return redirect(url_for("stock"))
    return render_template("production.html", form=form, user=current_user)


@app.route("/stock")
@login_required
def stock():
    produced = Production.query.filter_by(id=Production.id).all()
    return render_template("stock.html", produced=produced, user=current_user)


@app.route("/task_give/", methods=["GET", "POST"])
@app.route("/task_give", methods=["GET", "POST"])
@login_required
def task_give():
    task = []
    companies = []
    if request.method == "POST":
        if current_user.role == "admin" or current_user.role == "owner" and "assigned_user" in request.form:
            assigned_user = User.query.filter_by(
                email=request.form["assigned_user"]).first()
            if assigned_user:
                companies = ','.join(request.form.getlist('companies'))
                new_task = Tasks(
                    task_name=request.form["task"],
                    task_taker=request.form["task_taker"],
                    assigned_user=assigned_user,
                    now_time=now_uz,
                    deadline=request.form["deadline"],
                    company=request.form["company"],
                    companies=companies
                )
                existing_companies = new_task.company.split(
                    ',') if new_task.company else []
                for company in companies:
                    if company not in existing_companies:
                        existing_companies.append(company)
                new_task.company = ','.join(existing_companies)
                db.session.add(new_task)
                db.session.commit()
                task.append(new_task)
                socketio.emit('notification', {
                              'data': "Yangi topshiriq yuborildi. Qarab qo'y!!!"}, room=assigned_user.email)
                return redirect(url_for('task_give'))
            else:
                flash("User is not valid!", "error")
                return redirect(url_for("task_give"))
    else:
        if current_user.role == "admin" or current_user.role == "owner":
            task = Tasks.query.all()
        else:
            task = Tasks.query.join(User).filter(
                User.role == current_user.role).all()
    return render_template("task_give.html", tasks=task, user=current_user)


@app.route("/search")
def search():
    q = request.args.get("search")
    results = db.session.query(Tasks).filter(Tasks.task_name.contains(
        q) | Tasks.task_taker.contains(q) | Tasks.company.contains(q)).all()
    return render_template("search_results.html", results=results, user=current_user)


@app.route("/search_companies")
def search_companies():
    qc = request.args.get('qc')
    companies = Tasks.query.filter(Tasks.company.contains(qc)).all()
    return render_template("search_companies.html", companies=companies)


# @app.route('/orgsearch')
# def orgsearch():
#     result = Application.start(r'c:/users/user/desktop/555')
#     return f"Script output: {result}"


@app.route("/search_external", methods=["GET", "POST"])
def search_external():
    orginfo = request.form.get("orginfo")
    if request.method == "POST":
        if orginfo is not None:
            url = f"https://uzorg.info/search/main/{orginfo}/"
            page = requests.get(url, proxies={})
            soup = BeautifulSoup(page.content, "html.parser")
            results = soup.find_all(attrs={"class": "mb-1"})
            results_text = [result.get_text() for result in results]
            orgdata = Orgdata(orgresults=results_text)
            db.session.add(orgdata)
            db.session.commit()
            return render_template("search_external.html", user=current_user, orgcompany=Orgdata.query.all())
    else:
        return render_template("search_external.html", user=current_user, orgcompany=Orgdata.query.all())


@app.route("/sign_up/", methods=["GET", "POST"])
@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email")
        fullname = request.form.get("fullname")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        comment = str(password1)
        role = request.form.get("role")
        user = User.query.filter_by(email=email).first()
        if user:
            flash("This email is already taken. Use another!", category="error")
        elif len(email) < 5:
            flash("At least 6 characters for email, please!", category="error")
        elif password1 != password2:
            flash("Passwords don't match", category="error")
        elif len(password1) < 5:
            flash("At least 6 characters for password, please", category="error")
        else:
            new_user = User(email=email, fullname=fullname, comment=comment, role=role,
                            password=generate_password_hash(password1, method="sha256"))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created successfully!", category="success")
            return redirect(url_for("login"))
    return render_template("sign_up.html", user=current_user)


@app.route("/login/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully", category="success")
                login_user(user, remember=True)
                return redirect(url_for("index"))
            else:
                flash("Incorrect password", category="error")
        else:
            flash("This user doesn't exist", category="error")
    return render_template("login.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/logout_all')
def logout_all():
    app.config['SECRET_KEY'] = os.urandom(24)
    return redirect(url_for('login'))


@app.route("/users/")
@app.route("/users")
def users():
    users = User.query.filter_by(email=User.email).all()
    return render_template("users.html", user=current_user, users=users)


@app.route("/create_all")
def create_all():
    db.create_all()
    return "All tables are created!!!"


@app.route('/run_calculator')
def run_calculator():
    return jsonify(command="run_calculator")
