

var f = function(q){
    var x = 10;
    return function(){
        return q*x;
    }
}


var f2 = f(9);

log(f2())