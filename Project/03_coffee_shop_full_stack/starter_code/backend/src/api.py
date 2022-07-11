import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
@requires_auth('get:drinks')
def get_drinks(payload):
    drinks = Drink.query.all()
    
    return jsonify({
        {
            "success": True,
            "drinks": [drink.short() for drink in drinks]
        }
    }, 200)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_details(payload):
    drinks = Drink.query.all()
    
    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    }, 200)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
# def add_drink():
    req_body = request.get_json()
    print(type(req_body))
    title = req_body['title']
    recipe = req_body['recipe']
    
    if not title or not recipe:
        abort(400)

    error = None
    try:
        drink = Drink(title=title, recipe=recipe)
        db.session.add(drink)
        db.session.flush()
        drink_id = drink.id
        db.session.commit()
    except Exception as e:
        print(e)
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)

    return jsonify({
        "success": True,
        "drinks": {
            "id": drink_id,
            "title": title,
            "recipe": recipe
        }
    }, 200)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):
    req_body = request.get_json()
    if not req_body:
        abort(400)
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    
    error = None
    try:
        for key, val in req_body.items():
            setattr(drink, key, val)
    except Exception as e:
        print(e)
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)

    return jsonify({
        "success": True,
        "drinks": [{
            "id": drink.id,
            "title": drink.title,
            "recipe": drink.recipe
        }]
    }, 200)
    

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    
    error = None
    try:
        drink.delete()
    except Exception as e:
        print(e)
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    return jsonify({
        "success": True,
        "delete": id
    }, 200)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def authentication_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }, error.status_code)
