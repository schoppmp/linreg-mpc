%clear;

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

[X] = cgd2(A,b,it);

err = [];
res = [];
for i = 1:it
	err(end+1) = norm(z-X(:,i));
	res(end+1) = norm(A*X(:,i) - b);
end;
figure;
subplot(2,2,1); hold all; plot([1:it],err);
subplot(2,2,2); hold all; plot([1:it],res);
subplot(2,2,3); hold all; plot([1:it],log10(err));
subplot(2,2,4); hold all; plot([1:it],log10(res));

[X,Y] = cgdscl(A,b,it);

err = [];
res = [];
for i = 1:it
	err(end+1) = norm(z-X(:,i));
	res(end+1) = norm(A*X(:,i) - b);
end;
subplot(2,2,1); plot([1:it],err);
subplot(2,2,2); plot([1:it],res);
subplot(2,2,3); plot([1:it],log10(err));
subplot(2,2,4); plot([1:it],log10(res));

%buildInstrumentedMex cgd2 -args {zeros(d,d),zeros(d,1),0} -histogram -o cgd2_inst
%cgd2_inst(A,b,it);
%showInstrumentationResults cgd2_inst -defaultDT numerictype(1,64) -proposeFL

buildInstrumentedMex cgdscl -args {zeros(d,d),zeros(d,1),0} -histogram -o cgdscl_inst
cgdscl_inst(A,b,it);
showInstrumentationResults cgdscl_inst -defaultDT numerictype(1,64) -proposeFL
