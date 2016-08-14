function [X] = cgd2(A,b,it) %#codegen
dim = size(A,2);

X = zeros(dim,it);

x = zeros(dim,1);
r = zeros(dim,1);
d = zeros(dim,1);
nrprev = 0;
nd = 0;
alpha = 0;
beta = 0;

r(:) = b - A*x;
d(:) = r;
for i = 1:it
    alpha(:) = (r'*r)/(d'*A*d);
    x(:) = x + alpha*d;
    nrprev(:) = r'*r;
    % NOTE true residual can be substituted by approx residual
    r(:) = b - A*x;
    beta(:) = (r'*r)/nrprev;
    d(:) = r + beta*d;
    %nd(:) = sqrt(d'*d);
    %d(:) = d/nd;
    X(:,i) = x;
end;

