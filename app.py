from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo, DESCENDING
from bson.objectid import ObjectId
import re
import os
import bcrypt


app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'recipe_builder'
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.getenv("SECRET_KEY")


mongo = PyMongo(app)

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    """Home page gets 6 recipes that are most popular based on views"""
    recipes = mongo.db.recipes.find().sort([('views', DESCENDING)]).limit(6)
   
    return render_template('index.html', recipes=recipes)


"""User Login Form"""
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users =mongo.db.users
        login_user = users.find_one({'name' : request.form['username']})
        
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            flash('Invalid username/password combination')
    return render_template('login.html')
    


"""User Logout"""  
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
    
    
"""User Registration Form"""    
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        flash('That username already exists! Please choose another')

    return render_template('register.html')


"""Get all recipes"""
@app.route('/get_recipes')
def get_recipes():
    return render_template("recipes.html", recipes=mongo.db.recipes.find())


"""Add recipe form"""  
@app.route('/add_recipe')
def add_recipe():
    return render_template('addrecipe.html', 
                            categories=mongo.db.category.find(),
                            allergens=mongo.db.allergen.find(),
                            serves=mongo.db.serves.find(),
                            measurements=mongo.db.measurements.find(),
                            preparation=mongo.db.preparation.find())
                            
 
"""Submit recipe to database"""
@app.route('/insert_recipe', methods=['POST'])
def insert_recipe():
    recipes=mongo.db.recipes
    recipes.insert_one({
        'recipe_name':request.form['recipe_name'],
        'brief_description':request.form['brief_description'],
        'category_name':request.form['category_name'],
        'allergen_name':request.form['allergen_name'],
        'prep_time':request.form['prep_time'],
        'cook_time':request.form['cook_time'],
        'amount_serves':request.form['amount_serves'],
        'image_file': request.form['image_file'],
        'ingredients':request.form['ingredients'],
        'method_description':request.form['method_description'],
        'views': 0,
        'user':session['username']
    })
    return redirect(url_for('get_recipes'))


"""Edit recipe form"""
@app.route('/edit_recipe/<recipe_id>')
def edit_recipe(recipe_id):
    the_recipe=mongo.db.recipes.find_one({"_id":ObjectId(recipe_id)})
    all_categories = mongo.db.category.find()
    all_allergens = mongo.db.allergen.find()
    all_serves = mongo.db.serves.find()
    return render_template('editrecipe.html',
                            recipe=the_recipe,
                            categories=all_categories,
                            allergens=all_allergens,
                            serves=all_serves)
            

"""Submit edited recipe to database"""
@app.route('/update_recipe/<recipe_id>', methods=["POST"])
def update_recipe(recipe_id):
    recipe = mongo.db.recipes
    recipe.update({'_id':ObjectId(recipe_id)},
    {
        'recipe_name':request.form.get('recipe_name'),
        'brief_description':request.form.get('brief_description'),
        'category_name':request.form.get('category_name'),
        'allergen_name':request.form.get('allergen_name'),
        'prep_time':request.form.get('prep_time'),
        'cook_time':request.form.get('cook_time'),
        'amount_serves':request.form.get('amount_serves'),
        'image_file': request.form.get('image_file'),
        'ingredients':request.form.get('ingredients'),
        'method_description':request.form.get('method_description'),
        'user':session['username']
    })
    return redirect(url_for('get_recipes'))
    

"""Delete recipe from database"""    
@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    if request.method == 'GET':
        flash("Are you sure you want to delete this recipe?")
        
    mongo.db.recipes.remove({'_id':ObjectId(recipe_id)})
    return redirect (url_for('get_recipes'))


"""View full recipe"""    
@app.route('/view_recipe/<recipe_id>')
def view_recipe(recipe_id):
    recipe = mongo.db.recipes
    recipe.find_one_and_update(
        {'_id': ObjectId(recipe_id)},
        {'$inc': {'views': 1}}
    )
    recipe_db = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    return render_template("viewrecipe.html", recipe=recipe_db)


"""Search Database for Recipes"""
@app.route('/find_recipes', methods=['GET', 'POST'])
def find_recipes():
    if request.method=='POST':
        
        # get the search term
        search_term = request.form.get("search_term")
        
        #  create the index
        mongo.db.recipes.create_index( [("$**", 'text')] )
        
         # search with the search term that came through the form
        cursor = mongo.db.recipes.find({ "$text": { "$search": search_term } })
        recipes = [recipe for recipe in cursor]
        
        # send recipes to page
        return render_template('search.html', recipes=recipes, query=search_term)
        
    return render_template('search.html')
    
    

if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)
