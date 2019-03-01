#!/usr/bin/python
from flask import (
    Flask,
    url_for,
    request,
    flash,
    render_template,
    jsonify,
    redirect
)
from database_setup import Base, GiftCategory, GiftItems, Owner
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import AccessTokenCredentials
from oauth2client.client import FlowExchangeError
from flask import session as user_session
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask import make_response
import random
import httplib2
import string
import requests
import os
import dummydata
import json
# accessing client id from client_secret.json
fh = open('client_secret.json')
SECRET_DATA = json.loads(fh.read())
CLIENT_ID = SECRET_DATA.get('web').get('client_id')
fh.close()


app = Flask(__name__)
APP_NAME = 'eGifts'


engine = create_engine('sqlite:///gifts.db')
Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))


# Home page for eGifts and it shows recent 10 gift items
@app.route('/')
@app.route('/egifts')
@app.route('/egifts/')
def home():
    """Display recent 10 items if available.

    if empty create and display 2 items.
    """
    user_status, user_email, user_id = login_status()
    items = recentItems()
    if not items:
        # checking items is empty
        flash("There is no items but i'm adding dummy data", "warning")
        data = dummydata.getDummy()
        owner = Owner(
            email='eGifts@gmail.com',
            image='http://chittagongit.com//images/\
            user-profile-icon/user-profile-icon-5.jpg'
            )
        session.add(owner)
        session.commit()
        for name, each in zip(data[0], data[1]):
            category = GiftCategory(name=name, id_owner=owner.id_owner)
            session.add(category)
            session.commit()
            item = GiftItems(
                name=each[0],
                madeIn=each[1],
                img_url=each[2],
                additional_info=each[3],
                price=each[4],
                id_category=category.id_category
                )
            session.add(item)
            session.commit()
    items = recentItems()
    return render_template(
        'child_layout.html',
        category_name=None,
        items=items
        )


item = None
category = None


# Gives available gift items from all the gift categories as JSON format
@app.route('/egifts/all.json')
def all_json():
    """Gives the JSON data for all the items."""
    items = session.query(GiftItems).all()
    return jsonify(Items=[each.serialize for each in items])


# Adding new gift category
@app.route('/egifts/category/new', methods=['GET', 'POST'])
def newCategory():
    """If user login creates new category.

    Otherwise redirect to home.
    """
    user_status, user_email, user_id = login_status()
    if user_status:
        # checking if user login
        if request.method == "GET":
            return render_template('newCategory.html', id_owner=user_id)
        if request.method == "POST":
            category_name = request.form['category_name']
            new_category = GiftCategory(name=category_name, id_owner=user_id)
            session.add(new_category)
            session.commit()
            flash(
                u"" + str(category_name) + "category created successfully",
                "success"
                )
            return redirect(url_for('modify_category'))
    else:
        flash(u'Please login and try again', "warning")
        return redirect(url_for('home'))


# It provides gift categories with options(edit/delete) for modification.
@app.route('/egifts/category/modify')
def modify_category():
    "It give access to modification options user owned categories."
    user_status, user_email, user_id = login_status()
    if user_status:
        categories = session.query(GiftCategory).filter_by(
            id_owner=user_id
            ).all()
        if categories:
            return render_template(
                'modifyCategory.html',
                categories=categories
                )
        else:
            flash(u'You dont have a categories to modify', 'danger')
            return render_template(
                'modifyCategory.html',
                categories=categories
                )
    else:
        flash('Please login and try again', "warning")
        return redirect(url_for('home'))


# Shows all available items in given gift category
@app.route('/egifts/category/<int:idOfCategory>')
@app.route('/egifts/category/<int:idOfCategory>/')
def show_each_category_items(idOfCategory):
    "Shows all available items in given category."
    category = session.query(GiftCategory).filter_by(
        id_category=idOfCategory
        ).one_or_none()
    items = session.query(GiftItems).filter_by(
        id_category=idOfCategory
        ).all()
    if not category:
        flash(u"wrong category selection, check once ", "danger")
        return redirect(url_for('home'))
    if items:
        return render_template(
            'child_layout.html',
            items=items,
            category_name=category.name
            )
    else:
        flash(
            u"There is no items in  " + str(category.name) + " Category",
            "danger"
            )
        return redirect(url_for('home'))


# It gives the form for editing given gift category and save changes
@app.route('/egifts/category/<int:idOfCategory>/edit', methods=['GET', 'POST'])
def edit_category(idOfCategory):
    "Apply changes to given category."
    user_status, user_email, user_id = login_status()
    if not user_status:
        flash('Please login and try again', "danger")
        return redirect(url_for('home'))
    else:
        if request.method == "GET":
            category = session.query(GiftCategory).filter_by(
                id_owner=user_id,
                id_category=idOfCategory
                ).one_or_none()
            if category:
                return render_template('editCategory.html', category=category)
            flash(u'you are selected wrong category', 'danger')
            return redirect(url_for('home'))
        elif request.method == "POST":
            category = session.query(GiftCategory).filter_by(
                id_owner=user_id,
                id_category=idOfCategory
                ).one_or_none()
            if category:
                owner_idof_category = category.id_owner
                if owner_idof_category != user_id:
                    flash(
                        u"you are not a owner to delete " + str(category.name),
                        'warning'
                        )
                    return redirect(url_for('modify_category'))
                new_category_name = request.form['category_newname']
                old_category_name = category.name
                category.name = new_category_name
                session.add(category)
                session.commit()
                flash(
                    u"category updated successfully from " +
                    str(old_category_name) +
                    " to " +
                    str(new_category_name)
                    )
                return redirect(url_for('modify_category'))
            else:
                flash(u"You are selected wrong category ", "danger")
                return redirect(url_for('modify_category'))
        flash(u'something is wrong go to home ', 'warning')
        return redirect(url_for('modify_category'))


# To remove specified gift category if available
@app.route('/egifts/category/<int:idOfCategory>/delete', methods=['GET'])
def deleteCategory(idOfCategory):
    """Removes given category if available.

    Otherwise alert flash message.
    """
    user_status, user_email, user_id = login_status()
    if not user_status:
        flash(u'Please login and try again', "warning")
        return redirect(url_for('modify_category'))
    if request.method == 'GET':
        category = session.query(GiftCategory).filter_by(
            id_category=idOfCategory
            ).one_or_none()
        if category:
            owner_idof_category = category.id_owner
            if owner_idof_category != user_id:
                flash(u"only owner can delete category", "warning")
                return redirect(url_for('modify_category'))
            else:
                name_category = category.name
                session.delete(category)
                session.commit()
                flash(
                    u"" +
                    str(name_category) +
                    " category deleted successfully",
                    'success'
                    )
                return redirect(url_for('modify_category'))
        else:
            flash(
                u"the selected category " + idOfCategory + " not available ",
                'warning'
                )
            return redirect(url_for('modify_category'))
    flash(u"something is wrong please try again", 'warning')
    return redirect(url_for('modify_category'))


# Gives the available items in given category as JSON format
@app.route('/egifts/category/<int:idOfCategory>.json')
def single_category_json(idOfCategory):
    "returns given category in JSON format."
    items = session.query(GiftItems).filter_by(
        id_category=idOfCategory
        ).all()
    return jsonify(Items=[each.serialize for each in items])


# Adding new gift item
@app.route('/egifts/item/new', methods=['GET', 'POST'])
def newItem():
    "Give access to add new item"
    user_status, user_email, user_id = login_status()
    if user_status:
        if request.method == 'GET':
            categories = session.query(GiftCategory).filter_by(
                id_owner=user_id
                ).all()
            if categories:
                return render_template(
                    'newGiftItem.html',
                    categories=categories
                    )
            else:
                flash(
                    u"you don't have categories to add new item," +
                    "create category and then add items",
                    "warning"
                    )
                return redirect(url_for('home'))
        elif request.method == 'POST':
            idOfCategory = request.form['categories']
            category = session.query(GiftCategory).filter_by(
                id_category=idOfCategory
                ).one_or_none()
            if not category:
                return (
                    "the selected category " +
                    idOfCategory +
                    " not available "
                    )
            owner_idof_category = category.id_owner
            if owner_idof_category != user_id:
                return (
                    "Owner idof category is  " +
                    str(owner_idof_category) +
                    " but login user id is " +
                    str(user_id)
                    )
            item_name = request.form['item_name']
            price = request.form['price']
            img_url = request.form['img_url']
            moreInfo = request.form['additional_info']
            madeIn = request.form['madeIn']
            item = GiftItems(
                name=item_name,
                madeIn=madeIn,
                img_url=img_url,
                additional_info=moreInfo,
                price=price,
                id_category=idOfCategory
            )
            session.add(item)
            session.commit()
            return redirect(url_for(
                'show_each_item',
                idOfCategory=idOfCategory,
                idOfItem=item.id_item
                ))
        else:
            flash(u'something is wrong  ', 'warning')
            return redirect(url_for('home'))
    else:
        flash(u'Please login and try again', "warning")
        return redirect(url_for('home'))


# Sending available gift categories, user login status and
# google sign in state to all templates
@app.context_processor
def inject_gift_categories():
    "Inject gift categories,user status and google state to all templates."
    categories = session.query(GiftCategory).all()
    user_login_state = login_status()
    state = get_g_state()
    if user_login_state[0]:
        # checking user login or not
        lstate = user_session['state']
    else:
        if state:
            lstate = state  # state id here
    return dict(
        categories_=categories,
        state=user_login_state,
        STATE=lstate
        )


# Shows the complete details of particular item
@app.route('/egifts/category/<int:idOfCategory>/<int:idOfItem>')
@app.route('/egifts/category/<int:idOfCategory>/<int:idOfItem>/')
def show_each_item(idOfCategory, idOfItem):
    """Display complete details of given item.

    If given item not available flash message.
    """
    category = session.query(GiftCategory).filter_by(
        id_category=idOfCategory).one_or_none()
    item = session.query(GiftItems).filter_by(
        id_category=idOfCategory,
        id_item=idOfItem).one_or_none()
    if item and category:
        user_status, user_email, user_id = login_status()
        return render_template(
            'giftItem.html',
            item=item,
            category=category,
            current_user=user_id
            )
    else:
        flash(u'items not found', 'danger')
        return redirect(url_for('home'))


# Edit particular gift item
@app.route(
    '/egifts/category/<int:idOfCategory>/<int:idOfItem>/edit',
    methods=['GET', 'POST']
    )
def edit_item(idOfCategory, idOfItem):
    "Give access to modify given item."
    user_status, user_email, user_id = login_status()
    if not user_status:
        flash(u"Please login and try again", "danger")
        return redirect(url_for('home'))
    else:
        category = session.query(GiftCategory).filter_by(
            id_category=idOfCategory
            ).one_or_none()
        item = session.query(GiftItems).filter_by(
            id_item=idOfItem,
            id_category=idOfCategory
            ).one_or_none()
        if ((not category) or (not item)):
            # checking given item or category not avaialble
            flash(u"There is no items what you specified", "danger")
            return redirect(url_for('home'))
        isItemOwner = isOwner(category, item, user_id)
        if not (isItemOwner):
            # checking user has right to modify
            flash(u"you are not owner for " + str(item.item_name), "warning")
            return redirect(url_for('home'))
        else:
            if request.method == "GET":
                categories = session.query(GiftCategory).filter_by(
                    id_owner=user_id
                    )
                return render_template(
                    'editGiftItem.html',
                    gift_item=item,
                    gift_category=category,
                    categories=categories
                    )
            if request.method == "POST":
                item_name = request.form['item_name']
                madein = request.form['made']
                price = request.form['price']
                img_url = request.form['img_url']
                newidOfCategory = request.form['categories']
                additional_info = request.form['additional_info']
                item.name = item_name
                item.price = price
                item.madeIn = madein
                item.id_category = newidOfCategory
                item.additional_info = additional_info
                session.add(item)
                session.commit()
                flash(u'Gift item updated successfully', "success")
                return redirect(url_for(
                    'show_each_item',
                    idOfCategory=newidOfCategory,
                    idOfItem=item.id_item
                    ))


# Gives the complete details of particular item as JSON format
@app.route('/egifts/category/<int:idOfCategory>/<int:idOfItem>.json')
def single_item_json(idOfCategory, idOfItem):
    "returns given item in JSON format."
    item = session.query(GiftItems).filter_by(
        id_category=idOfCategory,
        id_item=idOfItem
        ).all()
    return jsonify(Item=[i.serialize for i in item])


# To remove given item from given category
@app.route('/egifts/category/<int:idOfCategory>/<int:idOfItem>/delete')
def deleteItem(idOfCategory, idOfItem):
    """Removes given item if avaialble and if owner.

    Otherwise flash message.
    """
    user_status, user_email, user_id = login_status()
    if not user_status:
        flash(u"Please login and try again ", "warning")
        return redirect(url_for('home'))
    else:
        category = session.query(GiftCategory).filter_by(
            id_category=idOfCategory
            ).one_or_none()
        item = session.query(GiftItems).filter_by(
            id_item=idOfItem,
            id_category=idOfCategory
            ).one_or_none()
        if ((not category) or (not item)):
            # checking given item or category not avaialble
            flash(u"There is no items what you specified", "danger")
            return redirect(url_for('home'))
        isItemOwner = isOwner(category, item, user_id)
        if not (isItemOwner):
            flash(
                u"you are not a owner to delete  " +
                str(item.name),
                "danger"
                )
            return redirect(url_for('home'))
        name = item.name
        session.delete(item)
        session.commit()
        flash(
            u"Gift item " +
            str(name) +
            " deleted successfully",
            "success"
            )
        return redirect(url_for('home'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    "For google sign in."
    # Validate state token
    if request.args.get('state') != user_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError as e:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'
    url = url.format(str(access_token))
    h = httplib2.Http()
    stringdata = h.request(url, 'GET')[1].decode()
    result = json.loads(stringdata)
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = user_session.get('access_token')
    stored_gplus_id = user_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    user_session['access_token'] = credentials.access_token
    user_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    try:
        user_session['img_url'] = data['picture']
    except Exception:
        user_session['img_url'] = "None"
    user_session['email'] = data['email']
    image_url = user_session['img_url']
    user_status, user_email, user_id = login_status()
    if not user_status:
        create_owner()
    return jsonify(email=user_session['email'],
                   img=user_session['img_url'])
    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    "For disconnect the connected user."
    access_token = user_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user not connected.'
            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'
    url = url.format(str(user_session['access_token']))
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del user_session['access_token']
        del user_session['gplus_id']
        del user_session['email']
        del user_session['img_url']
        flash('Successfully disconnected.', 'success')
        return redirect(url_for('home'))
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'),
            400
            )
        response.headers['Content-Type'] = 'application/json'
        return response


def get_g_state():
    "Check the user connect with gmail or not."
    user_status, user_email, user_id = login_status()
    if user_status:
        return None
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    user_session['state'] = state
    return state


# For logout
@app.route('/egifts/logout')
def logout():
    user_status, user_email, user_id = login_status()
    if not user_status:
        flash("You already logout", "warning")
        return redirect(url_for('home'))
    return gdisconnect()


@app.route('/egifts/loginsuccess')
def loginsuccess():
    "Gives flash message once when login success."
    flash(u'welcome ' + str(login_status()[1]), 'success')
    return redirect(url_for('home'))


# Check the status of current login person
def login_status():
    """ It returns (True,email,id) of user if login.

    Else returns (False,None,None).
    """
    try:
        email = user_session.get('email')
    except Exception:
        email = None
    if email is None:
        return False, None, None
    owner = session.query(Owner).filter_by(email=email).one_or_none()
    if owner:
        return True, owner.email, owner.id_owner
    else:
        return False, None, None


# To store the owner details in table
def create_owner():
    "It creates owner."
    email = user_session['email']
    img_url = user_session['img_url']
    owner = Owner(email=email, image=img_url)
    session.add(owner)
    session.commit()


# check and return present user has owner for item or not
def isOwner(category, item, user_id):
    """ It checks the current login user

    has owner for item or not and

    returns True/False based on that.
    """
    owner_idof_category = category.id_owner
    category_idof_item = item.id_category
    condition1 = (category_idof_item == category.id_category)
    condition2 = (owner_idof_category == user_id)
    condition3 = (condition1 and condition2)
    return condition3


# return recently added 10 items
def recentItems():
    """ It returns top 10 recently added items. """
    items = session.query(GiftItems).order_by(
        GiftItems.id_item.desc()
        ).limit(10).all()
    return items


# For chrome cache
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


# handling browser cache
def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(
                app.root_path,
                endpoint,
                filename
                )
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
