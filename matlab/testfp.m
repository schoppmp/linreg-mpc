clear;

n = 1000;
d = 100;
%it = ceil(d/4);
%it = d;
it = 100;

sigmaY = 0.05;
x = randn(n,d);
for i = 1:d
    maxx = max(abs(x(:,i)));
    x(:,i) = x(:,i)/maxx;
end;
z = rand(d,1);
y = x*z + sigmaY*randn(n,1);

xx = x / sqrt(d*n);
yy = y / sqrt(d*n);
A = xx'*xx;
b = xx'*yy;
disp(cond(A));

sigmaR = 0.0001;
A = A + sigmaR*eye(d);
disp(cond(A));

[Xexp,Pexp,Gexp] = cgd1(A,b,it);

T = mytypes('fixed',32,32-4);
Afp = cast(A,'like',T);
bfp = cast(b,'like',T);
zfp = cast(z,'like',T);
[Xfp,Pfp,Gfp] = cgdfp(Afp,bfp,it,T);

disp(norm(double(Xfp-Xexp)));
disp(norm(double(Pfp-Pexp)));
disp(norm(double(Gfp-Gexp)));

err = [];
res = [];
obj = [];
for i = 1:it
	err(end+1) = norm(z-Xexp(:,i));
	res(end+1) = norm(x*Xexp(:,i) - y)^2/n + sigmaR*norm(Xexp(:,i))^2;
end;

% figure;
% subplot(2,2,1); hold all; plot([1:it],err);
% subplot(2,2,2); hold all; plot([1:it],res);
% subplot(2,2,3); hold all; plot([1:it],log10(err));
% subplot(2,2,4); hold all; plot([1:it],log10(res));

Xfp2db = double(Xfp);
errfp = [];
resfp = [];
for i = 1:it
	errfp(end+1) = norm(z-Xfp2db(:,i));
	resfp(end+1) = norm(x*Xfp2db(:,i) - y)^2/n + sigmaR*norm(Xfp2db(:,1))^2;
	%resfp(end+1) = norm(double(xfp*Xfp(:,i)) - double(yfp));
end;

% subplot(2,2,1); plot([1:it],errfp);
% subplot(2,2,2); plot([1:it],resfp);
% subplot(2,2,3); plot([1:it],log10(errfp));
% subplot(2,2,4); plot([1:it],log10(resfp));

figure;
subplot(2,2,1); hold all; plot([1:it],err); plot([1:it],errfp);
subplot(2,2,2); hold all; plot([1:it],res); plot([1:it],resfp);
subplot(2,2,3); hold all; plot([1:it],log10(err)); plot([1:it],log10(errfp));
subplot(2,2,4); hold all; plot([1:it],log10(res)); plot([1:it],log10(resfp));

%codegen cgdfp -args {Afp,bfp,it} -config:lib -report
%codegen cgd1 -args {A,b,it} -config:lib -report

% buildInstrumentedMex cgd1 -args {zeros(d,d),zeros(d,1),0} -histogram -o cgd1_inst
% [Xexp_mex,Pexp_mex,Gexp_mex] = cgd1_inst(A,b,it);
% showInstrumentationResults cgd1_inst -defaultDT numerictype(1,16) -proposeFL
 
 
