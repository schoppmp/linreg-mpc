clear;

d = 500;
it = d;
sigma1 = 0.1;
sigma2 = 0.0;
A = rand(d,d);
A = A*A';
A = A + sigma1*eye(d);
z = rand(d,1);
b = A*z;
A = A + sigma2*eye(d);
[X,P,G] = cgd1(A,b,it);

err = [];
res = [];
for i = 1:it
	err(end+1) = norm(z-X(:,i));
	res(end+1) = norm(A*X(:,i) - b);
end;
figure;
subplot(2,2,1); plot([1:it],err);
subplot(2,2,2); plot([1:it],res);
subplot(2,2,3); plot([1:it],log10(err));
subplot(2,2,4); plot([1:it],log10(res));

