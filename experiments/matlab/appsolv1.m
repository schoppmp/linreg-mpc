function [x] = appsolv1(A,b,it)
    q1 = b/sqrt(b'*b);
	[alpha,beta,Q] = lanczos1(A,q1,it);
    bbar = Q'*b;
	y = symtrisolv(alpha,beta,bbar);
	x = Q*y;
