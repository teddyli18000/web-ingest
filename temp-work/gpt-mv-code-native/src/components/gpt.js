import {PALETTE as P} from '../engine/palette.js';
import {easeOut} from '../engine/timing.js';

// Original code-native character. Coordinates are authored in a 1000×1000 local artboard.
const coat=new Path2D('M174 1000 C185 835 250 754 365 718 C430 698 455 664 466 610 L544 610 C556 666 580 699 648 719 C767 754 830 836 842 1000 Z');
const shirt=new Path2D('M391 725 C430 700 458 678 468 632 L540 632 C553 681 579 704 620 728 L573 1000 L430 1000 Z');
const neck=new Path2D('M454 646 C467 601 469 567 465 535 L543 535 C540 571 543 607 558 648 C535 687 478 687 454 646 Z');
const face=new Path2D('M351 296 C363 180 431 113 519 111 C615 111 680 189 673 315 C667 431 615 552 510 565 C414 558 351 448 351 296 Z');
const faceShade=new Path2D('M590 154 C650 198 677 259 668 337 C658 431 612 520 535 553 C579 498 596 439 592 372 C590 285 563 214 590 154 Z');
const hair=new Path2D('M337 315 C304 213 353 116 455 73 C534 39 651 72 706 157 C741 211 733 298 704 357 C694 274 663 236 617 208 C633 261 626 310 610 343 C592 269 554 221 507 193 C479 242 432 280 369 303 C359 359 352 406 364 459 C326 418 313 365 337 315 Z');
const fringe=new Path2D('M363 291 C393 251 437 227 492 189 C479 270 445 324 392 350 C450 333 512 296 548 229 C556 296 542 350 518 386 C559 349 595 300 616 220 C641 280 639 337 618 390 C599 443 563 489 510 518 C448 504 398 462 371 406 C350 361 348 324 363 291 Z');
const hairShade=new Path2D('M372 302 C414 274 459 236 493 194 C478 277 446 327 397 354 C443 345 496 318 533 268 C526 331 502 380 466 409 C430 397 397 378 374 348 Z');
const leftEyeTop=new Path2D('M405 366 Q442 342 479 367');
const leftEyeBottom=new Path2D('M409 372 Q442 388 476 371');
const rightEyeTop=new Path2D('M540 367 Q576 343 613 369');
const rightEyeBottom=new Path2D('M544 373 Q577 389 610 372');
const nose=new Path2D('M511 382 C505 402 505 414 516 421');
const mouth=new Path2D('M479 463 Q510 478 541 459');
const browL=new Path2D('M407 333 Q442 320 474 333');
const browR=new Path2D('M545 333 Q578 321 608 336');
const arm=new Path2D('M634 753 C704 742 780 712 852 662 C879 643 905 655 910 679 C914 700 895 717 873 727 C799 765 735 809 670 842 Z');
const hand=new Path2D('M846 662 C873 640 908 624 936 631 C956 636 955 653 938 661 L905 675 L946 667 C967 665 971 682 951 690 L910 699 L946 698 C967 700 966 718 946 721 L895 721 C878 714 859 697 846 680 Z');

function plate(d,path,fill,tx,ty,alpha,stroke=null,width=0){d.save(()=>{d.g.translate(tx,ty);d.path(path,{fill,stroke,width,alpha})})}
function strokePath(d,path,color,width,alpha){d.save(()=>{d.g.strokeStyle=color;d.g.lineWidth=width;d.g.lineCap='round';d.g.lineJoin='round';d.g.globalAlpha=alpha;d.g.stroke(path)})}

export function drawGPT(d,x,y,s,{alpha=1,assemble=1,pose='listen',look=0,blink=0}={}){
  const g=d.g,a=easeOut(assemble),sep=1-a;
  d.save(()=>{
    g.translate(x,y);g.scale(s,s);
    if(pose==='think')g.rotate(-.018);else if(pose==='reply')g.rotate(.012);

    // Three-register print logic: shadow/ink/color plates visibly converge during assembly.
    plate(d,coat,'rgba(23,32,51,.18)',-28*sep+12,20*sep+18,alpha*.65);
    plate(d,coat,P.ink,-120*sep,65*sep,alpha);
    plate(d,shirt,P.cobalt,78*sep,100*sep,alpha*.98);
    plate(d,neck,P.paper2,0,120*sep,alpha);
    plate(d,face,P.paper2,95*sep,45*sep,alpha);
    plate(d,faceShade,'rgba(126,165,245,.18)',95*sep,45*sep,alpha*a);
    plate(d,hair,P.white,-65*sep,-125*sep,alpha,P.ink2,4);
    plate(d,fringe,P.cobalt2,35*sep,-70*sep,alpha*.92);
    plate(d,hairShade,'rgba(47,102,213,.30)',35*sep,-70*sep,alpha*a);

    // Hair strand linework keeps the settled character from reading as a flat icon.
    const detail=alpha*a;
    d.line(402,187,378,286,{color:P.ink2,width:3,alpha:detail*.52});
    d.line(466,146,438,285,{color:P.ink2,width:3,alpha:detail*.45});
    d.line(562,153,575,284,{color:P.ink2,width:3,alpha:detail*.40});
    d.line(629,180,647,296,{color:P.ink2,width:3,alpha:detail*.34});

    // Four-petal clip is a character mark, deliberately not a company logo.
    const clipA=alpha*a;for(let k=0;k<4;k++){const ang=k*Math.PI/2;d.circle(690+Math.cos(ang)*21,214+Math.sin(ang)*21,14,{fill:k%2?P.gold:P.cobalt,alpha:clipA})}d.circle(690,214,9,{fill:P.white,alpha:clipA});

    const fa=alpha*Math.max(0,(a-.38)/.62);
    if(fa>0){
      const dx=look*10;
      d.save(()=>{
        g.translate(dx,0);
        strokePath(d,browL,P.ink2,4,fa*.52);strokePath(d,browR,P.ink2,4,fa*.52);
        if(blink>.55){
          strokePath(d,leftEyeTop,P.ink,6,fa);strokePath(d,rightEyeTop,P.ink,6,fa);
        }else{
          strokePath(d,leftEyeTop,P.ink,5,fa);strokePath(d,leftEyeBottom,P.ink2,2.2,fa*.50);
          strokePath(d,rightEyeTop,P.ink,5,fa);strokePath(d,rightEyeBottom,P.ink2,2.2,fa*.50);
          d.circle(444,367,7,{fill:P.cobalt,alpha:fa});d.circle(577,368,7,{fill:P.cobalt,alpha:fa});
          d.circle(446,365,2,{fill:P.white,alpha:fa});d.circle(579,366,2,{fill:P.white,alpha:fa});
        }
        strokePath(d,nose,P.ink2,2.5,fa*.38);strokePath(d,mouth,P.ink,4,fa*.88);
      });
      d.circle(419+dx,426,24,{fill:'rgba(230,106,92,.07)',alpha:fa});
      d.circle(600+dx,427,24,{fill:'rgba(230,106,92,.06)',alpha:fa});
    }

    if(pose==='reply'){
      plate(d,arm,P.ink,180*sep,50*sep,alpha*a);
      plate(d,hand,P.paper2,220*sep,10*sep,alpha*a,P.ink2,3);
      // Finger articulation: tiny authored lines rather than a mitten silhouette.
      d.line(1119,677,1150,668,{color:P.ink2,width:2.5,alpha:detail*.58});
      d.line(1122,690,1155,685,{color:P.ink2,width:2.5,alpha:detail*.52});
      d.line(1118,704,1150,703,{color:P.ink2,width:2.5,alpha:detail*.46});
    }

    // Garment structure and a restrained secondary cobalt seam.
    d.line(445,720,505,803,{color:P.paper,width:4,alpha:detail*.68});
    d.line(564,722,505,803,{color:P.paper,width:4,alpha:detail*.68});
    d.line(352,790,314,1000,{color:P.cobalt2,width:3,alpha:detail*.20});
    d.line(656,790,697,1000,{color:P.cobalt2,width:3,alpha:detail*.20});
  });
}

export function characterReveal(t,start=3.1,end=6.5){return {assemble:Math.max(0,Math.min(1,(t-start)/(end-start))),alpha:Math.max(0,Math.min(1,(t-start+.25)/.7))}}
