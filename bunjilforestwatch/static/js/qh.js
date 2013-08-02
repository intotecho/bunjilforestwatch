/* Copyright (c) 2013 the authors listed at the following URL, and/or
the authors of referenced articles or incorporated external code:
http://en.literateprograms.org/Quickhull_(Javascript)?action=history&offset=20120410175256

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Retrieved from: http://en.literateprograms.org/Quickhull_(Javascript)?oldid=18434
*/

function getDistant(cpt, bl) {
    var Vy = bl[1][0] - bl[0][0];
    var Vx = bl[0][1] - bl[1][1];
    return (Vx * (cpt[0] - bl[0][0]) + Vy * (cpt[1] -bl[0][1]))
}


function findMostDistantPointFromBaseLine(baseLine, points) {
    var maxD = 0;
    var maxPt = new Array();
    var newPoints = new Array();
    for (var idx in points) {
        var pt = points[idx];
        var d = getDistant(pt, baseLine);
        
        if ( d > 0) {
            newPoints.push(pt);
        } else {
            continue;
        }
        
        if ( d > maxD ) {
            maxD = d;
            maxPt = pt;
        }
    
    } 
    return {'maxPoint':maxPt, 'newPoints':newPoints}
}

var allBaseLines = new Array();
function buildConvexHull(baseLine, points) {
    
    allBaseLines.push(baseLine)
    var convexHullBaseLines = new Array();
    var t = findMostDistantPointFromBaseLine(baseLine, points);
    if (t.maxPoint.length) { // if there is still a point "outside" the base line
        convexHullBaseLines = 
            convexHullBaseLines.concat( 
                buildConvexHull( [baseLine[0],t.maxPoint], t.newPoints) 
            );
        convexHullBaseLines = 
            convexHullBaseLines.concat( 
                buildConvexHull( [t.maxPoint,baseLine[1]], t.newPoints) 
            );
        return convexHullBaseLines;
    } else {  // if there is no more point "outside" the base line, the current base line is part of the convex hull
        return [baseLine];
    }    
}
function getConvexHull(points) {
    //find first baseline
    var maxX, minX;
    var maxPt, minPt;
    for (var idx in points) {
        var pt = points[idx];
        if (pt[0] > maxX || !maxX) {
            maxPt = pt;
            maxX = pt[0];
        }
        if (pt[0] < minX || !minX) {
            minPt = pt;
            minX = pt[0];
        }
    }
    var ch = [].concat(buildConvexHull([minPt, maxPt], points),
                       buildConvexHull([maxPt, minPt], points))
    return ch;
}
function getRandomPoints(numPoint, xMax, yMax) {
    var points = new Array();
    var phase = Math.random() * Math.PI * 2;
    for (var i = 0; i < numPoint/2; i++) {
        var r =  Math.random()*xMax/4;
        var theta = Math.random() * 1.5 * Math.PI + phase;
        points.push( [ xMax /4 + r * Math.cos(theta), yMax/2 + 2 * r * Math.sin(theta) ] )
    }
    var phase = Math.random() * Math.PI * 2;
    for (var i = 0; i < numPoint/2; i++) {
        var r =  Math.random()*xMax/4;
        var theta = Math.random() * 1.5 * Math.PI + phase;
        points.push( [ xMax /4 * 3 +  r * Math.cos(theta), yMax/2 +  r * Math.sin(theta) ] )
    }
    return points
}


function plotBaseLine(baseLine,color) {
    var ctx = document.getElementById('qh_demo').getContext('2d');
    var pt1 = baseLine[0]
    var pt2 = baseLine[1];
    ctx.save()
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(pt1[0],pt1[1]);
    ctx.lineTo(pt2[0],pt2[1]);
    ctx.stroke();
    ctx.restore();
}   



var pts;

function qhPlotPoints() {
    ctx = document.getElementById('qh_demo').getContext('2d');
    ctx.clearRect(0,0,200,200);
    ctx.fillStyle = 'rgb(0,0,0)';
    pts = getRandomPoints(250,200,200);
    for (var idx in pts) {
        var pt = pts[idx];
        ctx.fillRect(pt[0],pt[1],2,2);
    }
}



function qhPlotConvexHull() {
    var ch = getConvexHull(pts);
    var eBL = allBaseLines[0];
    function plotIntermediateBL() {
        var l = allBaseLines.shift();
        if (l) {
            plotBaseLine(l, 'rgb(180,180,180)');
            setTimeout(plotIntermediateBL, 250);
        } else {
            for (var idx in ch) {    
                var baseLine = ch[idx];
                plotBaseLine(baseLine, 'rgb(255,0,0)');
            }
            plotBaseLine(eBL,'rgb(0,255,0)');
        }
    }
    plotIntermediateBL();
}
